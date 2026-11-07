import hashlib
import secrets
import time

import pytest

from test_vault import account, env
from vault import VaultError


def test_sharing_requires_owner_or_admin(env):
    vault, admin, _ = env
    owner = account(vault, admin, 'owner', 'Employee')
    other = account(vault, admin, 'other', 'Employee')
    guest = account(vault, admin, 'guest', 'Guest')
    fid = vault.upload(owner, 'notes.txt', b'sensitive')
    for token in (other, guest):
        with pytest.raises(VaultError):
            vault.set_shared(token, fid, True)
    vault.set_shared(owner, fid, True)
    assert vault.download(other, fid)[1] == b'sensitive'
    assert [f['id'] for f in vault.files(guest)] == [fid]
    vault.set_shared(admin, fid, False)
    with pytest.raises(VaultError):
        vault.download(other, fid)
    assert not vault.files(guest)
    assert vault.download(owner, fid)[1] == b'sensitive'


def test_verification_returns_proof_without_plaintext(env):
    vault, admin, _ = env
    guest = account(vault, admin, 'guest', 'Guest')
    fid = vault.upload(admin, 'example.txt', b'example content', True)
    result = vault.verify(admin, fid)
    assert result == {'name': 'example.txt', 'size': 15, 'sha256': hashlib.sha256(b'example content').hexdigest()}
    assert vault.activity(admin)[0]['action'] == 'verify_integrity'
    with pytest.raises(VaultError):
        vault.verify(guest, fid)
    with vault.db() as db:
        db.execute("UPDATE files SET digest=? WHERE id=?", ('0' * 64, fid))
    with pytest.raises(VaultError, match='Integrity'):
        vault.verify(admin, fid)


def test_activity_and_summary_do_not_leak_other_accounts(env):
    vault, admin, _ = env
    employee = account(vault, admin, 'employee', 'Employee')
    other = account(vault, admin, 'other', 'Employee')
    with pytest.raises(VaultError):
        vault.create_user(other, 'unauthorized', 'password-password', 'Admin')
    assert vault.security_summary(employee)['denied_24h'] == 0
    assert vault.security_summary(admin)['denied_24h'] == 1
    assert vault.security_summary(employee)['active_sessions'] == 1
    assert vault.security_summary(admin)['active_sessions'] == 3
    assert all(r['actor'] == 'employee' for r in vault.activity(employee))
    assert any(r['actor'] == 'other' for r in vault.activity(admin))
    assert vault.security_summary(employee)['key_fingerprint'] == vault.security_summary(admin)['key_fingerprint']


def test_revoking_own_other_sessions_preserves_other_accounts(env):
    vault, admin, _ = env
    employee = account(vault, admin, 'employee', 'Employee')
    uid = vault.user(employee)['id']
    alternate = secrets.token_urlsafe(32)
    with vault.db() as db:
        db.execute('INSERT INTO sessions VALUES(?,?,?)', (vault.token_hash(alternate), uid, time.time() + 1800))
    sessions = vault.own_sessions(employee)
    assert len(sessions) == 2
    assert sum(s['current'] for s in sessions) == 1
    assert all('token' not in s for s in sessions)
    assert vault.revoke_other_sessions(employee) == 1
    assert vault.user(employee)['id'] == uid
    assert vault.user(admin)['role'] == 'Admin'
    with pytest.raises(VaultError):
        vault.user(alternate)
