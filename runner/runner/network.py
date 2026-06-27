"""Network capture for network_assert graders.

The runner proxies the emulator's traffic through mitmproxy (run in dump mode,
writing a flow file). After the interaction window we parse the flow file into
lightweight `Flow` records the grader can assert against. We rely on mitmproxy's
`io.FlowReader`; no live addon code runs inside the grader.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from loguru import logger


@dataclass
class Flow:
    method: str
    url: str
    host: str
    path: str
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: str = ""
    status_code: int | None = None
    response_body: str = ""
    query: dict[str, list[str]] = field(default_factory=dict)


class NetworkCapture:
    """Parsed mitmproxy flows, with convenience matchers for graders."""

    def __init__(self, flows: list[Flow]) -> None:
        self.flows = flows

    def __len__(self) -> int:
        return len(self.flows)

    def to(self, path_substring: str) -> list[Flow]:
        return [f for f in self.flows if path_substring in f.path]

    def any_request(self, predicate) -> bool:
        return any(predicate(f) for f in self.flows)

    def with_header(self, name: str, value_substring: str = "") -> list[Flow]:
        name_l = name.lower()
        out = []
        for f in self.flows:
            for k, v in f.request_headers.items():
                if k.lower() == name_l and value_substring in v:
                    out.append(f)
                    break
        return out

    @classmethod
    def from_flow_file(cls, flow_path: Path) -> "NetworkCapture":
        """Parse a mitmproxy flow dump into Flow records."""
        flows: list[Flow] = []
        if not flow_path.is_file() or flow_path.stat().st_size == 0:
            return cls(flows)
        try:
            from mitmproxy import io as mio
        except Exception as exc:  # pragma: no cover - env without mitmproxy
            logger.error("mitmproxy not available to parse flows: {}", exc)
            return cls(flows)

        with flow_path.open("rb") as fh:
            reader = mio.FlowReader(fh)
            for flow in reader.stream():
                if getattr(flow, "request", None) is None:
                    continue
                req = flow.request
                parsed = urlparse(req.pretty_url)
                resp = getattr(flow, "response", None)
                flows.append(
                    Flow(
                        method=req.method,
                        url=req.pretty_url,
                        host=req.host,
                        path=parsed.path,
                        request_headers={k: v for k, v in req.headers.items()},
                        request_body=_safe_text(req.get_text(strict=False)),
                        status_code=resp.status_code if resp else None,
                        response_body=_safe_text(resp.get_text(strict=False)) if resp else "",
                        query=parse_qs(parsed.query),
                    )
                )
        logger.info("parsed {} flow(s) from {}", len(flows), flow_path)
        return cls(flows)


def _safe_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


class MitmProxyRecorder:
    """Run `mitmdump` for the duration of an interaction, writing a flow file."""

    def __init__(self, port: int, flow_path: Path, mitmdump_bin: str = "mitmdump") -> None:
        self._port = port
        self._flow_path = flow_path
        self._bin = mitmdump_bin
        self._proc: subprocess.Popen | None = None

    def __enter__(self) -> "MitmProxyRecorder":
        self._flow_path.parent.mkdir(parents=True, exist_ok=True)
        self._proc = subprocess.Popen(
            [
                self._bin,
                "-q",
                "--listen-port",
                str(self._port),
                "--set",
                "block_global=false",
                "-w",
                str(self._flow_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("mitmdump recording on :{} -> {}", self._port, self._flow_path)
        return self

    def __exit__(self, *exc) -> None:
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover - cleanup
                self._proc.kill()

    def capture(self) -> NetworkCapture:
        return NetworkCapture.from_flow_file(self._flow_path)
