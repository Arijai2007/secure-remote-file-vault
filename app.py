import hmac
import io
import os
from datetime import datetime, timezone

import pyotp
import qrcode
import streamlit as st

from vault import Vault, VaultError

st.set_page_config(page_title='CipherVault | Secure Remote File Vault', page_icon='🔐', layout='wide')
st.markdown('''<style>
.stApp {background:#0b1120;color:#e8edf7} [data-testid="stSidebar"] {background:#111b2e}
.block-container {padding-top:2.5rem;max-width:1250px}
h1,h2,h3 {letter-spacing:-.035em} [data-testid="stMetric"] {background:#142137;padding:20px;border:1px solid #283850;border-radius:14px}
div.stButton>button[kind="primary"] {background:#5ee4be;color:#082c24;border:0}
.eyebrow {color:#5ee4be;font-size:12px;letter-spacing:.18em;font-weight:700}
.subtitle {color:#9cacc5;margin-bottom:28px}
</style>''', unsafe_allow_html=True)


def config(name, default=''):
    value = os.environ.get(name)
    if value is not None:
        return value
    try:
        return str(st.secrets.get(name, default))
    except st.errors.StreamlitSecretNotFoundError:
        return default


@st.cache_resource
def open_vault(directory, master):
    return Vault(directory, master)


def enrollment(secret, username):
    uri = pyotp.TOTP(secret).provisioning_uri(username, issuer_name='CipherVault')
    image = io.BytesIO()
    qrcode.make(uri).save(image, format='PNG')
    st.image(image.getvalue(), width=220)
    st.caption('Scan with an authenticator app. Keep the setup key private.')
    st.code(secret, language=None)


def time_label(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%d %b %Y · %H:%M UTC')


st.markdown('<p class="eyebrow">DEFENSE IN DEPTH / SECURE WORKSPACE</p>', unsafe_allow_html=True)
st.title('CipherVault')
st.markdown('<p class="subtitle">Your files. Protected at every layer.</p>', unsafe_allow_html=True)

master = config('VAULT_MASTER_KEY')
if not master:
    st.info('This vault needs its deployment secrets before it can be opened.')
    st.markdown('Set `VAULT_MASTER_KEY` and `VAULT_BOOTSTRAP_TOKEN` in the host’s secret settings. '
                'Generate independent random values with `python setup_vault.py --generate-secrets`. '
                'See the repository deployment guide for the complete setup.')
    st.stop()

try:
    vault = open_vault(config('VAULT_DATA_DIR', 'data'), master)
except VaultError as exc:
    st.error(str(exc))
    st.stop()

if vault.is_empty():
    st.subheader('Create your first administrator')
    st.caption('Initial setup requires the private bootstrap token configured by the deployer.')
    supplied = st.text_input('Bootstrap token', type='password')
    expected = config('VAULT_BOOTSTRAP_TOKEN')
    if not expected or not supplied or not hmac.compare_digest(supplied, expected):
        st.stop()
    secret = st.session_state.setdefault('setup_totp', pyotp.random_base32())
    col1, col2 = st.columns(2)
    with col1:
        with st.form('setup'):
            username = st.text_input('Administrator username')
            password = st.text_input('Password (12+ characters)', type='password')
            confirm = st.text_input('Confirm password', type='password')
            code = st.text_input('Authenticator code', max_chars=6)
            submitted = st.form_submit_button('Initialize vault', type='primary')
    with col2:
        enrollment(secret, username or 'administrator')
    if submitted:
        try:
            if password != confirm:
                raise VaultError('Passwords do not match.')
            vault.bootstrap(username, password, secret, code)
            del st.session_state['setup_totp']
            st.rerun()
        except VaultError as exc:
            st.error(str(exc))
    st.stop()

if 'token' not in st.session_state:
    left, right = st.columns([1, 1], gap='large')
    with left:
        st.subheader('Welcome back')
        st.write('Sign in with your password and authenticator to unlock your workspace.')
        with st.form('signin'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            code = st.text_input('6-digit authenticator code', max_chars=6)
            login = st.form_submit_button('Unlock vault', type='primary', use_container_width=True)
        if login:
            try:
                st.session_state.token = vault.login(username, password, code)
                st.rerun()
            except VaultError as exc:
                st.error(str(exc))
    with right:
        st.subheader('Built for layered protection')
        st.info('01 · Password + TOTP authentication\n\n02 · Admin, Employee and Guest permissions\n\n'
                '03 · AES-256-GCM + RSA-3072 key protection\n\n04 · SHA-256 verification and audit history')
        st.caption('Sessions expire after 30 minutes. Five failed logins trigger a five-minute account lockout.')
    st.stop()

token = st.session_state.token
try:
    user = vault.user(token)
except VaultError as exc:
    st.session_state.clear()
    st.warning(str(exc))
    st.button('Return to sign in', on_click=st.rerun)
    st.stop()

with st.sidebar:
    st.header('🔐 CipherVault')
    st.caption('SECURE REMOTE FILE VAULT')
    pages = ['Overview', 'File vault', 'Security guide']
    if user['role'] == 'Admin':
        pages += ['Team access', 'Audit trail']
    page = st.radio('Workspace', pages, label_visibility='collapsed')
    st.divider()
    st.write(user['username'])
    st.caption(user['role'] + ' · MFA authenticated')
    if st.button('Lock & sign out', use_container_width=True):
        vault.logout(token)
        st.session_state.clear()
        st.rerun()

try:
    if page in ('Overview', 'File vault'):
        files = vault.files(token)
    if page == 'Overview':
        st.header('Workspace overview')
        st.caption('A clear view of the files you can access.')
        a, b, c, d = st.columns(4)
        a.metric('Accessible files', len(files))
        b.metric('Encrypted storage', f"{sum(f['size'] for f in files)/1048576:.2f} MiB")
        c.metric('Access role', user['role'])
        d.metric('Encryption', 'AES-256')
        st.subheader('Recent files')
        if files:
            st.dataframe([{'File': f['name'], 'Uploaded by': f['uploaded_by'], 'Size (KiB)': round(f['size']/1024, 1),
                           'Visibility': 'Team' if f['shared'] else 'Private', 'Uploaded': time_label(f['created'])}
                          for f in files[:8]], hide_index=True, use_container_width=True)
        else:
            st.info('Your vault is ready. Upload your first document from File vault.')
        st.subheader('Protection status')
        st.success('Password + TOTP verified · Role checks enabled · Authenticated encryption enabled')
        st.caption('VPN access is a hosting/network control. This dashboard cannot verify that your connection uses a VPN.')

    elif page == 'File vault':
        st.header('File vault')
        st.caption('Encrypted before storage. Verified before download.')
        if user['role'] in ('Admin', 'Employee'):
            with st.expander('＋ Upload a file', expanded=not files):
                with st.form('upload', clear_on_submit=True):
                    uploaded = st.file_uploader('Choose a document', help='Maximum 20 MiB. All file types supported.')
                    shared = st.checkbox('Share with the team', help='Employees can download. Guests can see metadata only.')
                    submit = st.form_submit_button('Encrypt & upload', type='primary')
                if submit:
                    if uploaded is None:
                        st.warning('Choose a file first.')
                    else:
                        vault.upload(token, uploaded.name, uploaded.getvalue(), shared)
                        st.rerun()
        search = st.text_input('Search files', placeholder='Find a file by name…')
        matches = [f for f in files if search.casefold() in f['name'].casefold()]
        if not matches:
            st.info('No files match this view.')
        for f in matches:
            with st.container(border=True):
                st.subheader(f['name'])
                st.caption(f"{f['size']/1024:.1f} KiB · {f['uploaded_by']} · {time_label(f['created'])} · "
                           + ('Team' if f['shared'] else 'Private'))
                with st.expander('Integrity fingerprint'):
                    st.code(f['digest'], language=None)
                if user['role'] != 'Guest':
                    if st.button('Verify & prepare download', key='prepare'+f['id']):
                        name, data = vault.download(token, f['id'])
                        st.download_button('Download verified file', data, file_name=name,
                                           mime='application/octet-stream', key='download'+f['id'], on_click='ignore')
                if user['role'] == 'Admin':
                    with st.expander('Delete file'):
                        confirm = st.checkbox('Permanently delete this encrypted file', key='confirm'+f['id'])
                        if st.button('Delete permanently', key='delete'+f['id'], disabled=not confirm):
                            vault.delete(token, f['id'])
                            st.rerun()
        if user['role'] == 'Guest':
            st.caption('Guest access permits shared file metadata only. Downloads and uploads are restricted.')

    elif page == 'Team access':
        st.header('Team access')
        st.caption('Provision accounts and control workspace access.')
        st.dataframe(vault.users(token), hide_index=True, use_container_width=True)
        with st.form('new_user'):
            st.subheader('Create an account')
            username = st.text_input('New username')
            password = st.text_input('Initial password (12+ characters)', type='password')
            role = st.selectbox('Role', Vault.ROLES, index=1)
            create = st.form_submit_button('Create account', type='primary')
        if create:
            secret = vault.create_user(token, username, password, role)
            st.success('Account created. Deliver these enrollment details privately to the user now.')
            enrollment(secret, username)
            st.warning('The setup key is shown only in this response. The user must enroll an authenticator before logging in.')
        st.subheader('Account status')
        users = [u for u in vault.users(token) if u['id'] != user['id']]
        if users:
            selected = st.selectbox('Account', users, format_func=lambda u: u['username'])
            if st.button('Deactivate account' if selected['active'] else 'Reactivate account'):
                vault.set_active(token, selected['id'], not selected['active'])
                st.rerun()

    elif page == 'Audit trail':
        st.header('Audit trail')
        st.caption('Most recent 1,000 security events. Timestamps are UTC.')
        logs = vault.logs(token)
        for row in logs:
            row['at'] = time_label(row['at'])
        st.dataframe(logs, hide_index=True, use_container_width=True)
        import csv
        export = io.StringIO()
        writer = csv.DictWriter(export, fieldnames=['id', 'at', 'actor', 'action', 'target', 'outcome'])
        writer.writeheader()
        writer.writerows(logs)
        st.download_button('Export audit CSV', export.getvalue(), 'audit.csv', 'text/csv')

    elif page == 'Security guide':
        st.header('How your vault is protected')
        st.markdown('''
1. **Network access:** deploy behind WireGuard and bind the application to the VPN interface. Community Cloud is an internet-accessible demonstration deployment.
2. **Authentication:** bcrypt password hashes, encrypted TOTP seeds, one-use authenticator codes, login lockout and expiring server-side sessions.
3. **Authorization:** every vault operation checks the current account and its role on the server. Private files are accessible to their owner and administrators.
4. **Hybrid encryption:** a fresh AES-256-GCM key encrypts each file. RSA-3072 with OAEP/SHA-256 wraps each key. The RSA private key is encrypted with the deployment master key.
5. **Integrity:** GCM authentication rejects modified ciphertext; an additional SHA-256 check validates decrypted file content.
6. **Accountability:** successful and denied vault actions are recorded in SQLite. Administrators can inspect and export the audit trail.

**Role policy**

| Capability | Admin | Employee | Guest |
|---|---|---|---|
| List files | All | Own + shared | Shared metadata |
| Upload | Yes | Yes | No |
| Download | All | Own + shared | No |
| Delete | Yes | No | No |
| Manage users / audit | Yes | No | No |

**Operational limits:** this is an educational prototype. Audit records are not tamper-proof against the server operator. File names and hashes remain visible in the database. Keep encrypted storage and the master key in separate backups. Community Cloud local storage is ephemeral; use the documented persistent-volume deployment for durable files. Account recovery requires an administrator; master-key loss makes encrypted data unrecoverable.
''')
except VaultError as exc:
    st.error(str(exc))

st.divider()
st.caption('Secure Remote File Vault · VPN / RBAC / Hybrid Cryptography · JIIT, Noida')
