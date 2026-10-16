"""Interactive lab playground: session REST + a WebSocket terminal bridge.

The terminal spawns a PTY running `settings.lab_shell_command` and relays bytes
over the WebSocket. The default command is a shell inside the backend container
(a safe placeholder that works anywhere); on a KVM host set the command to
attach to the session device, e.g. `adb -s %(serial)s shell`, and the same
bridge gives the learner a live adb/frida shell on the emulator.
"""

from __future__ import annotations

import asyncio
import fcntl
import os
import shlex
import signal
import struct
import subprocess
import termios

from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_or_create_solo_user
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.lab import LabSessionCreate, LabSessionView
from app.services import instance_config, lab_session

router = APIRouter(prefix="/lab", tags=["lab"])


def _ensure_enabled(db: Session) -> None:
    if not (settings.lab_enabled and instance_config.lab_enabled(db)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "the lab playground is disabled")


def _view(sess) -> LabSessionView:
    """Serialize a session, resolving the visual stream URL for this device."""
    stream = settings.lab_stream_url or None
    if stream and "%(serial)s" in stream:
        stream = stream % {"serial": sess.device_serial or ""}
    return LabSessionView(
        id=sess.id,
        task_id=sess.task_id,
        status=sess.status,
        device_serial=sess.device_serial,
        expires_at=sess.expires_at,
        stream_url=stream,
    )


@router.post("/sessions", response_model=LabSessionView)
def start_session(
    body: LabSessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LabSessionView:
    _ensure_enabled(db)
    return _view(lab_session.create(db, user, body.task_id))


@router.get("/sessions/current", response_model=LabSessionView)
def current_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LabSessionView:
    _ensure_enabled(db)
    s = lab_session.get_active(db, user)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active lab session")
    return _view(s)


@router.delete("/sessions/current", status_code=status.HTTP_204_NO_CONTENT)
def end_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    _ensure_enabled(db)
    lab_session.end(db, user)


# ── WebSocket terminal bridge ───────────────────────────────────────────────


def _resolve_ws_user(token: str | None, db: Session) -> User | None:
    """Authenticate a WebSocket caller. Browsers can't set Authorization on a
    WebSocket, so the access token is passed as a query param (solo mode needs
    none). Returns None if the caller can't be resolved."""
    if instance_config.effective_solo_mode(db):
        return get_or_create_solo_user(db)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user = db.get(User, int(payload["sub"]))
    except (TypeError, ValueError):
        return None
    return user if user and user.is_active else None


def _lab_container_running() -> bool:
    """True if the isolated lab container is up and reachable via docker."""
    if not settings.lab_container:
        return False
    try:
        out = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", settings.lab_container],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0 and out.stdout.strip() == "true"


def _resolve_command(serial: str | None, user_id: int, solo: bool) -> list[str] | None:
    """Build the terminal command. Prefer an exec into the isolated lab
    container (no backend secrets); fall back to a placeholder shell only in
    solo mode. Returns None when no safe shell is available (hosted + no lab),
    so we never drop a learner into the secret-bearing backend container."""
    inner = settings.lab_shell_command
    if "%(serial)s" in inner:
        inner = inner % {"serial": serial or ""}

    if _lab_container_running():
        # Per-user scratch dir inside the isolated workstation.
        workdir = f"/work/{user_id}"
        bootstrap = f"mkdir -p {shlex.quote(workdir)} && cd {shlex.quote(workdir)} && exec {inner}"
        return ["docker", "exec", "-i", settings.lab_container, "bash", "-lc", bootstrap]

    if solo:
        # Single local operator on their own machine: the placeholder shell in
        # the backend container is acceptable (no other users to protect from).
        return shlex.split(inner)

    # Hosted with no lab workstation: refuse rather than expose backend secrets.
    return None


@router.websocket("/terminal")
async def terminal(
    ws: WebSocket,
    session_id: int = Query(...),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    if not (settings.lab_enabled and instance_config.lab_enabled(db)):
        await ws.close(code=1008)
        return
    user = _resolve_ws_user(token, db)
    if user is None:
        await ws.close(code=1008)
        return
    sess = lab_session.get_for_terminal(db, session_id, user)
    if sess is None:
        await ws.close(code=1008)
        return

    solo = instance_config.effective_solo_mode(db)
    argv = _resolve_command(sess.device_serial, user.id, solo)
    if argv is None:
        await ws.accept()
        await ws.send_text(
            "\r\n[lab] no isolated lab workstation is running. Start it with "
            "`docker compose --profile lab up -d lab`.\r\n"
        )
        await ws.close(code=1011)
        return

    await ws.accept()

    # Spawn the command on a PTY so interactive tools (frida, adb shell) behave.
    master_fd, slave_fd = os.openpty()
    # Sensible default window size; the client can resize via a control message.
    _set_winsize(master_fd, 40, 120)
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True,
        )
    except FileNotFoundError:
        await ws.send_text(f"\r\n[lab] command not found: {argv[0]}\r\n")
        await ws.close(code=1011)
        os.close(master_fd)
        os.close(slave_fd)
        return
    os.close(slave_fd)

    loop = asyncio.get_running_loop()
    await ws.send_text(f"\r\n[lab session {sess.id} · task {sess.task_id}] connected\r\n")

    async def pty_to_ws() -> None:
        try:
            while True:
                data = await loop.run_in_executor(None, _safe_read, master_fd)
                if not data:
                    break
                await ws.send_text(data.decode(errors="replace"))
        except Exception:  # noqa: BLE001 - client gone / fd closed
            pass

    reader = asyncio.create_task(pty_to_ws())
    try:
        while True:
            msg = await ws.receive_text()
            if msg.startswith("\x00resize:"):
                _handle_resize(master_fd, msg)
                continue
            os.write(master_fd, msg.encode())
    except Exception:  # noqa: BLE001 - normal disconnect
        pass
    finally:
        reader.cancel()
        try:
            proc.send_signal(signal.SIGHUP)
        except ProcessLookupError:
            pass
        os.close(master_fd)
        logger.info("lab terminal for session {} closed", sess.id)


def _safe_read(fd: int) -> bytes:
    try:
        return os.read(fd, 4096)
    except OSError:
        return b""


def _set_winsize(fd: int, rows: int, cols: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def _handle_resize(fd: int, msg: str) -> None:
    # Control message format: "\x00resize:<cols>,<rows>"
    try:
        cols, rows = (int(x) for x in msg[len("\x00resize:") :].split(","))
        _set_winsize(fd, rows, cols)
    except (ValueError, OSError):
        pass
