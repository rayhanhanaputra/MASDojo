"""Admin instance-settings endpoints: the runtime-tuning reset.

The first registered user is the bootstrap admin, so `auth_headers` is an admin
here and can reach the /admin routes.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

# The shipped defaults (an independent oracle — deliberately not read from the
# model, so a regression in either place is caught).
_TUNING_DEFAULTS = {
    "lab_session_ttl_min": 60,
    "lab_mem_limit": "512m",
    "lab_cpu_limit": "1.5",
    "lab_pids_limit": 256,
    "lab_stream_url": "",
    "grading_job_timeout_sec": 420,
    "mentor_rate_limit_per_hour": 30,
}


def test_reset_tuning_restores_defaults_and_leaves_other_settings(client: TestClient, auth_headers):
    # Move several non-tuning settings AND every tuning field off their defaults.
    # The non-tuning ones (registration, lab toggles, device pool) must survive a
    # reset — this guards against a future field being wrongly added to
    # TUNING_FIELDS.
    client.patch(
        "/admin/settings",
        json={
            "registration_open": False,
            "lab_enabled": False,
            "lab_allow_device_hosted": True,
            "lab_emulator_image": "ghcr.io/x/emu:test",
        },
        headers=auth_headers,
    )
    changed = client.patch(
        "/admin/settings",
        json={
            "lab_session_ttl_min": 5,
            "lab_mem_limit": "2g",
            "lab_cpu_limit": "4",
            "lab_pids_limit": 1024,
            "lab_stream_url": "https://x/%(serial)s",
            "grading_job_timeout_sec": 1200,
            "mentor_rate_limit_per_hour": 99,
        },
        headers=auth_headers,
    )
    assert changed.status_code == 200
    assert changed.json()["lab_session_ttl_min"] == 5

    reset = client.post("/admin/settings/reset-tuning", headers=auth_headers)
    assert reset.status_code == 200
    body = reset.json()

    # Every tuning field is back to its shipped default…
    for field, default in _TUNING_DEFAULTS.items():
        assert body[field] == default, field
    # …but none of the unrelated settings we changed are touched.
    assert body["registration_open"] is False
    assert body["lab_enabled"] is False
    assert body["lab_allow_device_hosted"] is True
    assert body["lab_emulator_image"] == "ghcr.io/x/emu:test"


def test_tuning_defaults_satisfy_patch_validation_bounds():
    """Drift guard: the reset path writes column defaults straight to the row,
    bypassing the PATCH schema's ge/le/max_length bounds. Assert every default is
    still valid input to that schema, so the validated and reset write paths can
    never diverge (a tightened bound without a matching default bump fails here)."""
    from app.models.instance_config import TUNING_FIELDS, InstanceConfig
    from app.schemas.admin import InstanceConfigUpdate

    columns = InstanceConfig.__table__.columns
    defaults = {field: columns[field].default.arg for field in TUNING_FIELDS}
    validated = InstanceConfigUpdate(**defaults)  # raises if any default is out of bounds
    for field, value in defaults.items():
        assert getattr(validated, field) == value


def test_reset_tuning_requires_admin(client: TestClient):
    # A second (non-first) account is a plain learner, so admin routes 403.
    client.post(
        "/auth/register",
        json={"email": "admin-boot@example.com", "display_name": "A", "password": "password123"},
    )
    client.post(
        "/auth/register",
        json={"email": "nobody@example.com", "display_name": "N", "password": "password123"},
    )
    token = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "password123"}
    ).json()["access_token"]
    r = client.post("/admin/settings/reset-tuning", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
