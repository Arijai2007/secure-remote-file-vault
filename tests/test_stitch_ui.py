import pyotp
import pytest
from streamlit.testing.v1 import AppTest

from vault import Vault


@pytest.fixture
def workspace(monkeypatch, tmp_path):
    key = 'test-master-key-of-at-least-32-characters'
    monkeypatch.setenv('VAULT_MASTER_KEY', key)
    monkeypatch.setenv('VAULT_DATA_DIR', str(tmp_path))
    vault = Vault(tmp_path, key)
    secret = pyotp.random_base32()
    vault.bootstrap('admin', 'correct-password-123', secret, pyotp.TOTP(secret).now())
    token = vault.login('admin', 'correct-password-123', pyotp.TOTP(secret).now())
    return vault, token


def file_page(token):
    app = AppTest.from_file('app.py', default_timeout=15)
    app.session_state['token'] = token
    app.run()
    app.sidebar.radio[0].set_value('File vault').run()
    assert not app.exception
    return app


def test_inspector_follows_filtered_accessible_files(workspace):
    vault, token = workspace
    vault.upload(token, 'report.pdf', b'report')
    vault.upload(token, 'photo.png', b'photo', True)
    app = file_page(token)
    selector = next(s for s in app.selectbox if s.label == 'Inspect file')
    assert set(selector.options) == {'photo.png', 'report.pdf'}
    next(s for s in app.selectbox if s.label == 'File type').select('Document').run()
    assert next(s for s in app.selectbox if s.label == 'Inspect file').options == ['report.pdf']
    assert any(c.value == '845e91831319e89c4d656bdb80c278ac09a7230d61e5dfd2e1b1fbb436ac8917' for c in app.code)
    next(t for t in app.text_input if t.label == 'Search files').set_value('absent').run()
    assert not app.exception
    assert not any(s.label == 'Inspect file' for s in app.selectbox)


def test_batch_verify_reports_tampered_file_and_preserves_good_files(workspace):
    vault, token = workspace
    vault.upload(token, 'good.txt', b'good')
    bad_id = vault.upload(token, 'bad.txt', b'bad')
    with vault.db() as db:
        db.execute('UPDATE files SET digest=? WHERE id=?', ('0' * 64, bad_id))
    app = file_page(token)
    next(b for b in app.button if b.label == 'Batch verify SHA-256').click().run()
    assert not app.exception
    assert any('1 verified' in s.value for s in app.success)
    assert any('bad.txt' in e.value for e in app.error)
    assert len(vault.files(token)) == 2


def test_guest_inspector_cannot_verify_or_download(workspace):
    vault, admin = workspace
    secret = vault.create_user(admin, 'guest', 'correct-password-123', 'Guest')
    token = vault.login('guest', 'correct-password-123', pyotp.TOTP(secret).now())
    vault.upload(admin, 'shared.txt', b'public metadata', True)
    vault.upload(admin, 'private.txt', b'private content')
    app = file_page(token)
    assert next(s for s in app.selectbox if s.label == 'Inspect file').options == ['shared.txt']
    assert not any(b.label in {'Batch verify SHA-256', 'Prepare download', 'Verify integrity',
                               'Verify selected file', 'Prepare selected download'} for b in app.button)
    assert not app.get('download_button')
