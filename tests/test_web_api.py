"""HTTP adapter keeps Vault's identity and role boundary intact."""
import pyotp
from fastapi.testclient import TestClient

import web_api


def test_web_setup_login_file_roles_and_audit(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULT_MASTER_KEY", "test-master-key-of-at-least-32-characters")
    monkeypatch.setenv("VAULT_BOOTSTRAP_TOKEN", "private-bootstrap-token")
    monkeypatch.setenv("VAULT_DATA_DIR", str(tmp_path))
    web_api.get_vault.cache_clear()
    client = TestClient(web_api.app)
    assert client.get("/api/status").json() == {"initialized": False}
    assert client.post("/api/setup/begin", json={"bootstrap_token": "wrong"}).status_code == 403
    enrollment = client.post("/api/setup/begin", json={"bootstrap_token": "private-bootstrap-token"}).json()
    setup = {"bootstrap_token": "private-bootstrap-token", "enrollment": enrollment["enrollment"],
             "username": "admin", "password": "strong-password-123", "code": pyotp.TOTP(enrollment["secret"]).now()}
    assert client.post("/api/setup/complete", json=setup).status_code == 200
    assert client.get("/api/status").json() == {"initialized": True}
    # The vault's replay behavior is tested separately; clear its bootstrap step to exercise the API session.
    with web_api.get_vault().db() as db:
        db.execute("UPDATE users SET last_step=-1 WHERE username='admin'")
    login = client.post("/api/login", json={"username": "admin", "password": setup["password"], "code": setup["code"]})
    assert login.status_code == 200
    csrf = login.json()["csrf"]
    assert client.post("/api/files", files={"file": ("sample.txt", b"secret")}).status_code == 403
    upload = client.post("/api/files?shared=true", files={"file": ("sample.txt", b"secret")}, headers={"X-CSRF-Token": csrf})
    assert upload.status_code == 200
    file_id = upload.json()["id"]
    assert client.post(f"/api/files/{file_id}/verify", headers={"X-CSRF-Token": csrf}).json()["sha256"]
    assert client.get(f"/api/files/{file_id}/download").content == b"secret"
    assert client.get("/api/audit/status").json()["valid"] is True
    assert client.get("/api/monitoring/demo").status_code == 200
    member = client.post("/api/users", json={"username": "guest", "password": "guest-password-123", "role": "Guest"},
                         headers={"X-CSRF-Token": csrf})
    assert member.status_code == 200
    guest = TestClient(web_api.app)
    guest_login = guest.post("/api/login", json={"username": "guest", "password": "guest-password-123",
                                                 "code": pyotp.TOTP(member.json()["totp_secret"]).now()})
    assert guest_login.status_code == 200
    assert len(guest.get("/api/files").json()) == 1
    assert guest.get(f"/api/files/{file_id}/download").status_code == 400
    assert guest.get("/api/audit").status_code == 400
    web_api.get_vault.cache_clear()
