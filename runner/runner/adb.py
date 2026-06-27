"""Thin adb wrapper used by graders and the runner orchestration."""

from __future__ import annotations

import subprocess
from pathlib import Path

from loguru import logger


class AdbError(RuntimeError):
    pass


class AdbClient:
    """Run adb commands against a specific emulator serial."""

    def __init__(self, serial: str, adb_bin: str = "adb", default_timeout: int = 60) -> None:
        self._serial = serial
        self._adb = adb_bin
        self._timeout = default_timeout

    def _run(self, args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
        cmd = [self._adb, "-s", self._serial, *args]
        logger.debug("adb: {}", " ".join(cmd))
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - timing
            raise AdbError(f"adb command timed out: {' '.join(args)}") from exc

    def shell(self, command: str, timeout: int | None = None) -> str:
        """Run `adb shell <command>` and return stdout (raises on non-zero)."""
        proc = self._run(["shell", command], timeout=timeout)
        if proc.returncode != 0:
            raise AdbError(f"adb shell failed ({proc.returncode}): {proc.stderr.strip()}")
        return proc.stdout

    def shell_ok(self, command: str, timeout: int | None = None) -> bool:
        """Run a shell command, returning True on exit code 0."""
        return self._run(["shell", command], timeout=timeout).returncode == 0

    def install(self, apk_path: Path, timeout: int = 180) -> None:
        proc = self._run(["install", "-r", "-g", str(apk_path)], timeout=timeout)
        if proc.returncode != 0 or "Success" not in proc.stdout:
            raise AdbError(f"apk install failed: {proc.stdout.strip()} {proc.stderr.strip()}")

    def uninstall(self, package: str) -> None:
        self._run(["uninstall", package])

    def pull(self, remote: str, local: str) -> Path:
        proc = self._run(["pull", remote, local])
        if proc.returncode != 0:
            raise AdbError(f"adb pull failed: {proc.stderr.strip()}")
        return Path(local)

    def launch_app(self, package: str, activity: str | None = None) -> None:
        target = f"{package}/{activity}" if activity else package
        if activity:
            self.shell(f"am start -n {target}")
        else:
            self.shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")

    def wait_for_device(self, timeout: int = 120) -> None:
        proc = self._run(["wait-for-device"], timeout=timeout)
        if proc.returncode != 0:
            raise AdbError("device did not come online")

    def logcat_dump(self, since: str | None = None) -> str:
        args = ["logcat", "-d"]
        if since:
            args += ["-T", since]
        return self._run(args).stdout

    def clear_logcat(self) -> None:
        self._run(["logcat", "-c"])
