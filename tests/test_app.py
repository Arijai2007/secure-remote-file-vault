from streamlit.testing.v1 import AppTest


def test_configuration_screen(monkeypatch):
    monkeypatch.setenv('VAULT_MASTER_KEY', '')
    app = AppTest.from_file('app.py', default_timeout=15).run()
    assert not app.exception
    assert app.title[0].value == 'CipherVault'


def test_bootstrap_screen(monkeypatch, tmp_path):
    monkeypatch.setenv('VAULT_MASTER_KEY', 'test-master-key-of-at-least-32-characters')
    monkeypatch.setenv('VAULT_BOOTSTRAP_TOKEN', 'test-bootstrap')
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    app = AppTest.from_file('app.py', default_timeout=15).run()
    assert not app.exception
    app.text_input[0].set_value('test-bootstrap').run()
    assert not app.exception
    assert any(x.label == 'Administrator username' for x in app.text_input)


def test_admin_login_and_workspace(monkeypatch, tmp_path):
    import pyotp
    from vault import Vault
    key = 'test-master-key-of-at-least-32-characters'
    monkeypatch.setenv('VAULT_MASTER_KEY', key)
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    vault = Vault(tmp_path, key)
    secret = pyotp.random_base32()
    vault.bootstrap('admin', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    app = AppTest.from_file('app.py', default_timeout=15).run()
    app.text_input[0].set_value('admin')
    app.text_input[1].set_value('correct-password-123')
    app.text_input[2].set_value(pyotp.TOTP(secret).now())
    app.button[0].click().run()
    assert not app.exception
    assert any(h.value == 'Workspace overview' for h in app.header)
    for page in ['File vault', 'Team access', 'Audit trail', 'Threat monitoring', 'My account', 'Security guide']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
        if page == 'Threat monitoring':
            next(b for b in app.button if b.label == 'Run synthetic AI demo').click().run()
            assert not app.exception
            assert len(app.dataframe) == 1


def test_file_filters_sharing_and_integrity_controls(monkeypatch, tmp_path):
    import pyotp
    from vault import Vault
    key = 'test-master-key-of-at-least-32-characters'
    monkeypatch.setenv('VAULT_MASTER_KEY', key)
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    vault = Vault(tmp_path, key)
    secret = pyotp.random_base32()
    vault.bootstrap('admin', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    token = vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    fid = vault.upload(token, 'report.pdf', b'not actually a pdf')
    vault.upload(token, 'photo.png', b'not actually an image', True)
    app = AppTest.from_file('app.py', default_timeout=15)
    app.session_state['token'] = token
    app.run()
    assert not app.exception
    app.sidebar.radio[0].set_value('File vault').run()
    assert not app.exception
    next(s for s in app.selectbox if s.label == 'File type').select('Document').run()
    assert len([b for b in app.button if b.label == 'Verify integrity']) == 1
    next(b for b in app.button if b.label == 'Verify integrity').click().run()
    assert not app.exception
    assert any('Integrity verified' in s.value for s in app.success)
    next(b for b in app.button if b.label == 'Share with team').click().run()
    assert not app.exception
    assert next(f for f in vault.files(token) if f['id'] == fid)['shared'] == 1


def test_monitoring_ui_and_tampered_audit_state(monkeypatch, tmp_path):
    import pyotp
    from vault import Vault
    key = 'test-master-key-of-at-least-32-characters'
    monkeypatch.setenv('VAULT_MASTER_KEY', key)
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    vault = Vault(tmp_path, key)
    secret = pyotp.random_base32()
    vault.bootstrap('admin', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    token = vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    app = AppTest.from_file('app.py', default_timeout=30)
    app.session_state['token'] = token
    app.run()
    app.sidebar.radio[0].set_value('Threat monitoring').run()
    assert not app.exception
    assert any('Collect at least 30' in info.value for info in app.info)
    next(b for b in app.button if b.label == 'Run synthetic AI demo').click().run()
    assert not app.exception
    assert any('2 unusual' in warning.value for warning in app.warning)
    app.sidebar.radio[0].set_value('Audit trail').run()
    assert not app.exception
    assert any('Audit chain verified' in message.value for message in app.success)
    with vault.db() as db:
        db.execute("UPDATE audit SET actor='tampered' WHERE id=1")
    app.run()
    assert not app.exception
    assert any('mismatch' in message.value for message in app.error)
    app.sidebar.radio[0].set_value('Threat monitoring').run()
    assert not app.exception
    assert any('integrity failed' in message.value for message in app.error)


def test_real_ai_report_renders(monkeypatch, tmp_path):
    import time
    from unittest.mock import patch
    import pyotp
    from vault import Vault
    key = 'test-master-key-of-at-least-32-characters'
    monkeypatch.setenv('VAULT_MASTER_KEY', key)
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    vault = Vault(tmp_path, key)
    secret = pyotp.random_base32()
    vault.bootstrap('admin', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    token = vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    start = int(time.time() // 300) * 300 - 51 * 300
    for i in range(50):
        with patch('vault.time.time', return_value=float(start + i * 300 + 1)):
            with vault.db() as db:
                for j in range(1 + i % 4):
                    vault.audit(db, 'admin', 'download', str(j), bytes_count=1000 + i)
    app = AppTest.from_file('app.py', default_timeout=30)
    app.session_state['token'] = token
    app.run()
    app.sidebar.radio[0].set_value('Threat monitoring').run()
    assert not app.exception
    assert any(m.label == 'Baseline user windows' and m.value == '40' for m in app.metric)
    assert len(app.dataframe) == 1
