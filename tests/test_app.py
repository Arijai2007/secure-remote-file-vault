from streamlit.testing.v1 import AppTest


def test_configuration_screen(monkeypatch):
    monkeypatch.setenv('VAULT_MASTER_KEY', '')
    app = AppTest.from_file('app.py').run()
    assert not app.exception
    assert app.title[0].value == 'CipherVault'


def test_bootstrap_screen(monkeypatch, tmp_path):
    monkeypatch.setenv('VAULT_MASTER_KEY', 'test-master-key-of-at-least-32-characters')
    monkeypatch.setenv('VAULT_BOOTSTRAP_TOKEN', 'test-bootstrap')
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    app = AppTest.from_file('app.py').run()
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
    app = AppTest.from_file('app.py').run()
    app.text_input[0].set_value('admin')
    app.text_input[1].set_value('correct-password-123')
    app.text_input[2].set_value(pyotp.TOTP(secret).now())
    app.button[0].click().run()
    assert not app.exception
    assert any(h.value == 'Workspace overview' for h in app.header)
    for page in ['File vault', 'Team access', 'Audit trail', 'Security guide']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
