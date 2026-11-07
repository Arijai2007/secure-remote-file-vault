import time

import pyotp
import pytest

from vault import Vault, VaultError


@pytest.fixture
def env(tmp_path):
    vault = Vault(tmp_path, 'a-test-master-key-with-more-than-32-characters')
    secret = pyotp.random_base32()
    vault.bootstrap('admin', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    token = vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    return vault, token, secret


def account(vault, admin, name, role):
    secret = vault.create_user(admin, name, 'correct-password-123', role)
    return vault.login(name, 'correct-password-123', pyotp.TOTP(secret).now())


def test_encrypted_roundtrip_and_restart(env):
    vault, admin, _ = env
    data = b'sensitive payroll information'
    fid = vault.upload(admin, '../payroll.txt', data)
    with vault.db() as db:
        row = db.execute('SELECT * FROM files').fetchone()
        assert data not in row['data']
        assert len(row['wrapped']) == 384
    reopened = Vault(vault.root, 'a-test-master-key-with-more-than-32-characters')
    assert reopened.download(admin, fid) == ('payroll.txt', data)


def test_rbac_and_private_file_isolation(env):
    vault, admin, _ = env
    employee = account(vault, admin, 'employee', 'Employee')
    colleague = account(vault, admin, 'colleague', 'Employee')
    guest = account(vault, admin, 'guest', 'Guest')
    private = vault.upload(employee, 'private.txt', b'private')
    shared = vault.upload(employee, 'shared.txt', b'shared', True)
    assert {f['id'] for f in vault.files(guest)} == {shared}
    assert {f['id'] for f in vault.files(colleague)} == {shared}
    assert vault.download(colleague, shared)[1] == b'shared'
    for operation in [lambda: vault.download(colleague, private), lambda: vault.download(guest, shared),
                      lambda: vault.upload(guest, 'x', b'x'), lambda: vault.delete(employee, private),
                      lambda: vault.create_user(employee, 'hacker', 'password-password', 'Admin'),
                      lambda: vault.logs(guest), lambda: vault.users(employee)]:
        with pytest.raises(VaultError):
            operation()
    assert sum(l['outcome'] == 'denied' for l in vault.logs(admin)) == 7
    vault.delete(admin, private)
    assert all(f['id'] != private for f in vault.files(admin))


@pytest.mark.parametrize('field', ['data', 'wrapped', 'digest', 'nonce'])
def test_tamper_detection(env, field):
    vault, admin, _ = env
    fid = vault.upload(admin, 'file.txt', b'top secret')
    with vault.db() as db:
        row = db.execute('SELECT * FROM files WHERE id=?', (fid,)).fetchone()
        value = '0' * 64 if field == 'digest' else bytes([row[field][0] ^ 1]) + row[field][1:]
        db.execute(f'UPDATE files SET {field}=? WHERE id=?', (value, fid))
    with pytest.raises(VaultError, match='Integrity'):
        vault.download(admin, fid)
    assert vault.logs(admin)[1]['outcome'] == 'denied'


def test_otp_replay_logout_expiry_and_deactivation(env):
    vault, admin, secret = env
    with pytest.raises(VaultError):
        vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    employee = account(vault, admin, 'employee', 'Employee')
    uid = vault.user(employee)['id']
    vault.set_active(admin, uid, False)
    with pytest.raises(VaultError):
        vault.user(employee)
    with pytest.raises(VaultError):
        vault.set_active(admin, vault.user(admin)['id'], False)
    other = account(vault, admin, 'other', 'Employee')
    with vault.db() as db:
        db.execute('UPDATE sessions SET expires=0 WHERE token=?', (vault.token_hash(other),))
    with pytest.raises(VaultError):
        vault.user(other)
    vault.logout(admin)
    with pytest.raises(VaultError):
        vault.user(admin)


def test_lockout_and_unknown_user(env):
    vault, admin, secret = env
    for _ in range(5):
        with pytest.raises(VaultError):
            vault.login('admin', 'wrong-password', '000000')
    with pytest.raises(VaultError, match='Too many'):
        vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    with pytest.raises(VaultError):
        vault.login('does-not-exist', 'wrong-password', '000000')


def test_master_key_bootstrap_and_input_validation(env):
    vault, admin, secret = env
    with pytest.raises(VaultError):
        Vault(vault.root, 'a-different-master-key-more-than-32-characters')
    with pytest.raises(VaultError):
        vault.bootstrap('another', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    for name, data in [('empty', b''), ('oversize', b'a' * (Vault.MAX_FILE + 1)), ('\x00bad', b'1')]:
        with pytest.raises(VaultError):
            vault.upload(admin, name, data)
    with pytest.raises(VaultError):
        vault.create_user(admin, 'new-user', 'short', 'Admin')
    with pytest.raises(VaultError):
        vault.create_user(admin, 'new-user', 'correct-password-123', 'Superuser')


def test_totp_seed_and_private_key_are_encrypted(env):
    vault, admin, secret = env
    with vault.db() as db:
        user = db.execute('SELECT * FROM users LIMIT 1').fetchone()
        pem = db.execute("SELECT value FROM settings WHERE name='rsa'").fetchone()[0]
        assert secret.encode() not in user['totp']
        assert user['password'].startswith(b'$2b$')
        assert b'BEGIN ENCRYPTED PRIVATE KEY' in pem
