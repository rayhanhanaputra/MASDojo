"""Android Virtual Device lifecycle: boot, wait-for-ready, snapshot, teardown.

To keep grading fast we boot the AVD once and restore from a cached snapshot
between jobs rather than cold-booting every time. The emulator is started
headless with no audio/window, hardware-accelerated via the host's KVM.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from loguru import logger

from runner.adb import AdbClient


class AvdError(RuntimeError):
    pass


class EmulatorManager:
    def __init__(
        self,
        avd_name: str,
        sdk_root: Path,
        serial: str,
        snapshot: str = "masdojo_clean",
    ) -> None:
        self._avd = avd_name
        self._sdk_root = sdk_root
        self._serial = serial
        self._snapshot = snapshot
        self._proc: subprocess.Popen | None = None
        self.adb = AdbClient(serial)

    @property
    def _emulator_bin(self) -> str:
        return str(self._sdk_root / "emulator" / "emulator")

    def boot(self, cold: bool = False, boot_timeout: int = 300) -> None:
        """Start the emulator headless and block until fully booted."""
        args = [
            self._emulator_bin,
            "-avd",
            self._avd,
            "-no-window",
            "-no-audio",
            "-no-boot-anim",
            "-gpu",
            "swiftshader_indirect",
        ]
        if cold:
            # Cold boot writable so we can install the mitmproxy CA into the
            # system trust store before snapshotting (enables HTTPS intercept).
            args += ["-no-snapshot-load", "-writable-system"]
        else:
            args += ["-read-only", "-snapshot", self._snapshot]
        logger.info("booting AVD {} (cold={})", self._avd, cold)
        self._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.adb.wait_for_device(timeout=boot_timeout)
        self._wait_until_booted(boot_timeout)
        logger.info("AVD {} booted", self._avd)

    def _wait_until_booted(self, timeout: int) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if self.adb.shell("getprop sys.boot_completed").strip() == "1":
                    return
            except Exception:  # noqa: BLE001 - device still coming up
                pass
            time.sleep(2)
        raise AvdError("emulator did not finish booting in time")

    def start_frida_server(self, frida_bin: str = "/opt/frida-server") -> None:
        """Push and launch frida-server so frida_assert graders can attach."""
        if not Path(frida_bin).exists():
            logger.warning("frida-server binary not found at {}; skipping", frida_bin)
            return
        try:
            self.adb._run(["root"])  # noqa: SLF001 - intentional privileged step
            self.adb._run(["push", frida_bin, "/data/local/tmp/frida-server"])  # noqa: SLF001
            self.adb.shell("chmod 755 /data/local/tmp/frida-server")
            self.adb.shell("nohup /data/local/tmp/frida-server >/dev/null 2>&1 &")
            time.sleep(2)
            logger.info("frida-server started on {}", self._serial)
        except Exception as exc:  # noqa: BLE001
            logger.warning("could not start frida-server: {}", exc)

    def install_mitm_ca(self, ca_path: str = "") -> None:
        """Install the mitmproxy CA into the system trust store (HTTPS intercept).

        Best-effort: requires a cold boot with -writable-system. Skipped quietly
        if the CA file or openssl isn't available. Run once before snapshotting.
        """
        import os
        import shutil
        import subprocess as sp

        ca = ca_path or os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.cer")
        if not Path(ca).is_file() or shutil.which("openssl") is None:
            logger.warning("mitmproxy CA not installed (missing CA file or openssl)")
            return
        try:
            digest = sp.run(
                ["openssl", "x509", "-inform", "PEM", "-subject_hash_old", "-in", ca],
                capture_output=True, text=True, check=True,
            ).stdout.splitlines()[0].strip()
            name = f"{digest}.0"
            self.adb._run(["root"])  # noqa: SLF001
            self.adb._run(["remount"])  # noqa: SLF001
            self.adb._run(["push", ca, f"/sdcard/{name}"])  # noqa: SLF001
            self.adb.shell(f"su 0 mv /sdcard/{name} /system/etc/security/cacerts/{name}")
            self.adb.shell(f"su 0 chmod 644 /system/etc/security/cacerts/{name}")
            logger.info("installed mitmproxy CA ({}) into the system store", name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("could not install mitmproxy CA: {}", exc)

    def save_snapshot(self) -> None:
        """Persist the current device state as the clean snapshot."""
        self._emu_console(f"avd snapshot save {self._snapshot}")
        logger.info("saved AVD snapshot '{}'", self._snapshot)

    def restore_snapshot(self) -> None:
        """Restore the clean snapshot, giving each job an identical device."""
        self._emu_console(f"avd snapshot load {self._snapshot}")
        logger.info("restored AVD snapshot '{}'", self._snapshot)

    def _emu_console(self, command: str) -> None:
        proc = subprocess.run(
            ["adb", "-s", self._serial, "emu", *command.split()],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise AvdError(f"emulator console command failed: {command}: {proc.stderr.strip()}")

    def shutdown(self) -> None:
        try:
            self._emu_console("kill")
        except AvdError:
            pass
        if self._proc is not None:
            try:
                self._proc.wait(timeout=15)
            except subprocess.TimeoutExpired:  # pragma: no cover - cleanup
                self._proc.kill()
        logger.info("AVD {} shut down", self._avd)
