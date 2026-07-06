"""Tests for the all-in-one target APK download endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings


def test_status_and_download_when_present(client: TestClient, tmp_path, monkeypatch):
    apk = tmp_path / "MASDojo.apk"
    apk.write_bytes(b"PK\x03\x04 not-a-real-apk")
    monkeypatch.setattr(settings, "target_apk_path", apk)

    status = client.get("/download/target-apk/status")
    assert status.status_code == 200
    body = status.json()
    assert body["available"] is True
    assert body["filename"] == "MASDojo.apk"
    assert body["size"] == apk.stat().st_size

    got = client.get("/download/target-apk")
    assert got.status_code == 200
    assert got.headers["content-type"] == "application/vnd.android.package-archive"
    assert got.content == b"PK\x03\x04 not-a-real-apk"


def test_status_and_download_when_missing(client: TestClient, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "target_apk_path", tmp_path / "nope.apk")

    status = client.get("/download/target-apk/status")
    assert status.status_code == 200
    assert status.json()["available"] is False

    assert client.get("/download/target-apk").status_code == 404


def test_download_is_public(client: TestClient, tmp_path, monkeypatch):
    # No Authorization header — the target APK is intentionally public.
    apk = tmp_path / "MASDojo.apk"
    apk.write_bytes(b"apk")
    monkeypatch.setattr(settings, "target_apk_path", apk)
    assert client.get("/download/target-apk/status").status_code == 200
    assert client.get("/download/target-apk").status_code == 200
