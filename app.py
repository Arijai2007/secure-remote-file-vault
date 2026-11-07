import csv
import hmac
import io
import math
import os
from datetime import datetime, timezone

import pyotp
import qrcode
import streamlit as st

from ui import (activity_item, banner, empty_state, eyebrow, file_heading,
                file_kind, format_size, load_styles, protection_card, brand,
                signin_art, workspace_identity, inspector_metadata)
from vault import Vault, VaultError

st.set_page_config(page_title='CipherVault | Secure Remote File Vault', page_icon='🔐', layout='wide')
load_styles()


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
    st.image(image.getvalue(), width=205)
    st.caption('Scan with an authenticator app. Keep the setup key private.')
    st.code(secret, language=None)


def time_label(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%d %b %Y · %H:%M UTC')


def footer():
    st.html('<div class="footer-line"><span>CIPHERVAULT · Secure Remote File Vault</span>'
            '<span>JIIT, Noida · VPN / RBAC / Hybrid cryptography</span></div>')


def protections():
    columns = st.columns(4)
    items = [('01', 'Prove your identity', 'Password and authenticator. Two checks before access.'),
             ('02', 'Access with purpose', 'Three roles, with permissions checked for every action.'),
             ('03', 'Keep files confidential', 'Unique AES-256 keys, protected with RSA-3072.'),
             ('04', 'Trust, then verify', 'Authenticated decryption, SHA-256 and an audit trail.')]
    for column, item in zip(columns, items):
        with column:
            protection_card(*item)


def role_table():
    st.markdown('''
| Capability | Admin | Employee | Guest |
|---|---|---|---|
| List files | All files | Own + team shared | Shared metadata |
| Upload | Yes | Yes | No |
| Download / verify | All files | Own + team shared | No |
| Change sharing | Any file | Own files | No |
| Delete | Yes | No | No |
| Manage accounts / audit | Yes | No | No |
| Manage own sessions | Yes | Yes | Yes |
''')
    st.caption('Administrators can access private files. Shared files are available to workspace members according to their role.')


def toast(message):
    st.session_state['notice'] = message
    st.rerun()


def csv_export(rows, fields):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r'))
                     else v for k, v in row.items()} for row in rows)
    return output.getvalue()


if 'token' not in st.session_state:
    brand()
master = config('VAULT_MASTER_KEY')
if not master:
    st.title('CipherVault')
    banner('WORKSPACE SETUP', 'A secure home for your files.',
           'A private workspace for your team’s documents, protected by layered security.')
    st.info('Your workspace is almost ready. The deployer needs to configure its private encryption secrets.')
    with st.expander('Deployment instructions'):
        st.write('Configure VAULT_MASTER_KEY and VAULT_BOOTSTRAP_TOKEN in your host’s secret settings. '
                 'Generate them privately with python setup_vault.py --generate-secrets. '
                 'Full instructions are in docs/DEPLOYMENT.md in the repository.')
    protections()
    footer()
    st.stop()

try:
    vault = open_vault(config('VAULT_DATA_DIR', 'data'), master)
except VaultError as exc:
    st.error(str(exc))
    st.stop()

if vault.is_empty():
    banner('WELCOME TO YOUR VAULT', 'Security starts with you.',
           'Create your administrator account and connect your authenticator. Your workspace will be ready in a few steps.',
           'FIRST-TIME SETUP')
    setup_tab, about_tab = st.tabs(['Set up your workspace', 'Explore the protection layers'])
    with setup_tab:
        left, right = st.columns([1.35, 1], gap='large')
        with left:
            st.subheader('Create your first administrator')
            st.caption('Start with the private bootstrap token from your deployment secrets.')
            supplied = st.text_input('Bootstrap token', type='password', placeholder='Enter your private setup token')
            expected = config('VAULT_BOOTSTRAP_TOKEN')
            authorized = bool(expected and supplied and hmac.compare_digest(supplied, expected))
            if authorized:
                secret = st.session_state.setdefault('setup_totp', pyotp.random_base32())
                with st.form('setup'):
                    username = st.text_input('Administrator username', placeholder='e.g. arihant')
                    password = st.text_input('Password (12+ characters)', type='password')
                    confirm = st.text_input('Confirm password', type='password')
                    code = st.text_input('Authenticator code', max_chars=6, placeholder='000000')
                    submitted = st.form_submit_button('Create secure workspace', type='primary', width='stretch')
                if submitted:
                    try:
                        if password != confirm:
                            raise VaultError('Passwords do not match.')
                        vault.bootstrap(username, password, secret, code)
                        del st.session_state['setup_totp']
                        st.rerun()
                    except VaultError as exc:
                        st.error(str(exc))
            elif supplied:
                st.warning('That setup token does not match. Check your deployment secrets.')
        with right:
            if authorized:
                st.subheader('Connect your authenticator')
                enrollment(secret, 'administrator')
            else:
                eyebrow('YOUR SETUP CHECKLIST')
                for item in ['1. Verify your private setup token', '2. Choose your administrator credentials',
                             '3. Scan the authenticator QR code', '4. Confirm a code and open your workspace']:
                    st.write(item)
                st.info('No default passwords. No public signup. You decide who gets access.')
    with about_tab:
        protections()
        st.caption('VPN protection depends on your hosting network. The public demo does not establish a VPN connection.')
    footer()
    st.stop()

if 'token' not in st.session_state:
    left, right = st.columns([1.35, 1], gap='large')
    with left:
        signin_art()
    with right:
        with st.container(key='signin-panel'):
            with st.form('signin'):
                st.subheader('Unlock Workspace')
                st.caption('Verify your password and authenticator to continue. Session lifetime: 30 minutes.')
                username = st.text_input('Username', placeholder='Your workspace username')
                password = st.text_input('Password', type='password', placeholder='Enter your password')
                code = st.text_input('6-digit authenticator code', max_chars=6, placeholder='000000')
                login = st.form_submit_button('Unlock your workspace', type='primary', width='stretch')
                st.caption('Lost credentials or authenticator? Contact your workspace administrator. Self-service signup is disabled.')
            if login:
                try:
                    st.session_state.token = vault.login(username, password, code)
                    st.rerun()
                except VaultError as exc:
                    st.error(str(exc))
    footer()
    st.stop()

token = st.session_state.token
try:
    user = vault.user(token)
except VaultError as exc:
    st.session_state.clear()
    st.warning(str(exc))
    if st.button('Return to sign in'):
        st.rerun()
    st.stop()

with st.sidebar:
    brand()
    pages = ['Overview', 'File vault', 'My account', 'Security guide']
    if user['role'] == 'Admin':
        pages = ['Overview', 'File vault', 'Team access', 'Audit trail', 'My account', 'Security guide']
    page = st.radio('Workspace', pages, label_visibility='collapsed')
    st.divider()
    st.write(user['username'])
    st.caption(user['role'] + ' · Two-factor authenticated')
    st.caption('Sessions automatically expire after 30 minutes.')
    if st.button('Lock & sign out', width='stretch'):
        vault.logout(token)
        st.session_state.clear()
        st.rerun()

workspace_identity(user['username'], user['role'])

if 'notice' in st.session_state:
    st.toast(st.session_state.pop('notice'), icon=':material/check_circle:')

try:
    if page in ('Overview', 'File vault'):
        files = vault.files(token)

    if page == 'Overview':
        st.header('Workspace overview')
        banner('YOUR FILES, UNDER CONTROL', 'A little order. A lot of protection.',
               'Manage your documents, keep access intentional and follow what happens in your workspace.',
               'MFA VERIFIED · ENCRYPTION ENABLED')
        a, b, c, d = st.columns(4)
        a.metric('Accessible files', len(files))
        b.metric('Encrypted file content', format_size(sum(f['size'] for f in files)))
        c.metric('Team-shared files', sum(bool(f['shared']) for f in files))
        d.metric('Your access role', user['role'])
        main, side = st.columns([1.7, 1], gap='large')
        with main:
            eyebrow('DOCUMENTS')
            st.subheader('Recently added')
            if files:
                st.dataframe([{'File': f['name'], 'Owner': f['uploaded_by'], 'Size': format_size(f['size']),
                               'Access': 'Team shared' if f['shared'] else 'Private'} for f in files[:6]],
                             hide_index=True, width='stretch')
            else:
                empty_state('A fresh start for your files', 'Your permitted uploads will appear here. Open File vault to get started.')
            eyebrow('FILE MIX')
            if files:
                kinds = sorted({file_kind(f['name']) for f in files})
                st.bar_chart({'Type': kinds, 'Files': [sum(file_kind(f['name']) == k for f in files) for k in kinds]},
                             x='Type', y='Files', color='#22d3ee', height=190)
            else:
                st.caption('Your file type breakdown appears after your first upload.')
        with side:
            eyebrow('WORKSPACE ACTIVITY' if user['role'] == 'Admin' else 'YOUR ACTIVITY')
            st.subheader('Recent events')
            for event in vault.activity(token, 5):
                activity_item(event['action'], event['actor'], time_label(event['at']), event['outcome'])
            eyebrow('AT A GLANCE')
            summary = vault.security_summary(token)
            st.caption(f"{summary['denied_24h']} denied actions in the past 24 hours · "
                       f"{summary['active_sessions']} active sessions " + ('in the workspace' if user['role'] == 'Admin' else 'for your account'))
        protections()

    elif page == 'File vault':
        st.header('File vault')
        st.caption('Encrypted on arrival. Verified on the way out.')
        a, b, c, d = st.columns(4)
        a.metric('Accessible objects', len(files))
        b.metric('Original file content', format_size(sum(f['size'] for f in files)))
        c.metric('Team shared', sum(bool(f['shared']) for f in files))
        d.metric('Private objects', sum(not f['shared'] for f in files))
        st.info(f"Security profile: {user['role']} · " +
                ('Shared metadata access. File content is restricted.' if user['role'] == 'Guest' else
                 'Downloads authenticate AES-GCM content and verify its SHA-256 digest.'))
        if user['role'] in ('Admin', 'Employee'):
            with st.expander('Upload a file', icon=':material/upload_file:', expanded=not files):
                with st.form('upload', clear_on_submit=True):
                    uploaded = st.file_uploader('Choose a document', help='Maximum 20 MiB. All file types supported. Files are stored encrypted.')
                    visibility = st.radio('Initial access', ['Private — you and administrators', 'Team — all workspace members'], horizontal=True)
                    st.caption('Team files can be downloaded by Employees and Admins. Guests see metadata only.')
                    submit = st.form_submit_button('Encrypt & upload', type='primary')
                if submit:
                    if uploaded is None:
                        st.warning('Choose a file first.')
                    else:
                        vault.upload(token, uploaded.name, uploaded.getvalue(), visibility.startswith('Team'))
                        toast('File encrypted and uploaded.')
        f1, f2, f3, f4 = st.columns([2.1, 1.2, 1.1, 1.2])
        search = f1.text_input('Search files', placeholder='Search by filename or owner…')
        visibility = f2.selectbox('Visibility', ['All accessible', 'Private', 'Team shared', 'Uploaded by me'])
        kind = f3.selectbox('File type', ['All types', 'Document', 'Spreadsheet', 'Image', 'Archive', 'Code', 'Other'])
        sort = f4.selectbox('Sort by', ['Newest first', 'Oldest first', 'Name A–Z', 'Largest first'])
        matches = [f for f in files if search.casefold() in (f['name'] + ' ' + f['uploaded_by']).casefold()
                   and (visibility != 'Private' or not f['shared'])
                   and (visibility != 'Team shared' or f['shared'])
                   and (visibility != 'Uploaded by me' or f['owner'] == user['id'])
                   and (kind == 'All types' or file_kind(f['name']) == kind)]
        sort_key, reverse = {'Newest first': ('created', True), 'Oldest first': ('created', False),
                             'Name A–Z': ('name', False), 'Largest first': ('size', True)}[sort]
        matches.sort(key=lambda f: f[sort_key].casefold() if sort_key == 'name' else f[sort_key], reverse=reverse)
        st.caption(f'{len(matches)} files · {format_size(sum(f["size"] for f in matches))} of file content')
        if not matches:
            empty_state('No files in this view', 'Try a different search or filter, or add your first file.')
        tools = st.columns([1, 1, 2])
        if user['role'] != 'Guest':
            if tools[0].button('Batch verify SHA-256', disabled=not matches, icon=':material/verified_user:'):
                verified = 0
                for item in matches:
                    try:
                        vault.verify(token, item['id'])
                        verified += 1
                    except VaultError as exc:
                        st.error(f"{item['name']}: {exc}")
                if verified:
                    st.success(f'{verified} verified · {len(matches) - verified} failed. Checked current filtered files.')
        if tools[1].button('Refresh manifest', icon=':material/refresh:'):
            st.rerun()
        listing, inspector = st.columns([1.8, 1], gap='large')
        with listing:
            with st.container(key='file-list'):
                total_pages = max(1, math.ceil(len(matches) / 8))
                current_page = st.selectbox('Page', list(range(1, total_pages + 1)), format_func=lambda p: f'{p} of {total_pages}') if total_pages > 1 else 1
                for f in matches[(current_page - 1) * 8:current_page * 8]:
                    with st.container(border=True, key='file-card-'+f['id']):
                        file_heading(f['name'], file_kind(f['name']), f['shared'])
                        st.caption(f"{format_size(f['size'])} · Added by {f['uploaded_by']} · {time_label(f['created'])}")
                        if user['role'] != 'Guest':
                            buttons = st.columns(2)
                            if buttons[0].button('Prepare download', key='prepare'+f['id'], width='stretch', icon=':material/download:'):
                                name, data = vault.download(token, f['id'])
                                st.download_button('Save verified file', data, file_name=name, mime='application/octet-stream',
                                                   key='download'+f['id'], on_click='ignore', type='primary')
                            if buttons[1].button('Verify integrity', key='verify'+f['id'], width='stretch', icon=':material/verified_user:'):
                                vault.verify(token, f['id'])
                                st.success('Integrity verified. Authentication tag and SHA-256 both match.')
                        with st.expander('File details & access'):
                            st.caption('SHA-256 fingerprint')
                            st.code(f['digest'], language=None)
                            st.caption('AES-256-GCM · RSA-3072 OAEP · File ID: ' + f['id'])
                            if user['role'] == 'Admin' or (user['role'] == 'Employee' and f['owner'] == user['id']):
                                st.caption('Sharing changes affect future access. Previously downloaded copies cannot be recalled.')
                                if st.button('Make private' if f['shared'] else 'Share with team', key='share'+f['id']):
                                    vault.set_shared(token, f['id'], not f['shared'])
                                    toast('File sharing updated.')
                            if user['role'] == 'Admin':
                                confirm = st.checkbox('I understand deletion is permanent', key='confirm'+f['id'])
                                if st.button('Delete file permanently', key='delete'+f['id'], disabled=not confirm):
                                    vault.delete(token, f['id'])
                                    toast('Encrypted file deleted.')

        with inspector:
            with st.container(key='crypto-inspector'):
                if matches:
                    selected_id = st.selectbox('Inspect file', [f['id'] for f in matches],
                                               format_func=lambda fid: next(f['name'] for f in matches if f['id'] == fid))
                    selected = next(f for f in matches if f['id'] == selected_id)
                    inspector_metadata(selected, time_label(selected['created']))
                    st.caption('SHA-256 checksum · recorded at upload')
                    st.code(selected['digest'], language=None)
                    st.caption('Access scope: ' + ('Team shared' if selected['shared'] else 'Private'))
                    if user['role'] != 'Guest':
                        if st.button('Verify selected file', key='inspector-verify', width='stretch', icon=':material/verified_user:'):
                            vault.verify(token, selected_id)
                            st.success('Verified now: GCM authentication and SHA-256 match.')
                        if st.button('Prepare selected download', key='inspector-download', type='primary', width='stretch'):
                            name, data = vault.download(token, selected_id)
                            st.download_button('Save selected verified file', data, file_name=name,
                                               mime='application/octet-stream', on_click='ignore', key='inspector-save')
                    st.caption('Previously downloaded copies cannot be recalled by changing access.')
                else:
                    st.subheader('Cryptographic Inspector')
                    st.caption('Choose a file from your accessible results to inspect its encryption metadata.')
        if user['role'] == 'Guest':
            st.info('You have metadata-only access. Ask your administrator if your work requires downloads.')

    elif page == 'Team access':
        st.header('Team access')
        st.caption('Give each person the access their work needs. Nothing is granted by default.')
        users = vault.users(token)
        a, b, c = st.columns(3)
        a.metric('Team members', len(users))
        b.metric('Active accounts', sum(u['active'] for u in users))
        c.metric('Access roles', '3')
        people, create_tab, policy = st.tabs(['Members', 'Add a member', 'Role permissions'])
        with people:
            query = st.text_input('Find a team member', placeholder='Search usernames…')
            st.dataframe([{'Username': u['username'], 'Role': u['role'], 'Status': 'Active' if u['active'] else 'Deactivated'}
                          for u in users if query.casefold() in u['username'].casefold()], hide_index=True, width='stretch')
            other_users = [u for u in users if u['id'] != user['id']]
            if other_users:
                st.subheader('Manage account access')
                selected = st.selectbox('Account', other_users, format_func=lambda u: u['username'])
                st.caption('Deactivation immediately revokes the account’s sessions. Its files remain in the vault.')
                if st.button('Deactivate account' if selected['active'] else 'Reactivate account'):
                    vault.set_active(token, selected['id'], not selected['active'])
                    toast('Account status updated.')
        with create_tab:
            with st.form('new_user'):
                st.subheader('Invite someone to the workspace')
                username = st.text_input('New username')
                password = st.text_input('Initial password (12+ characters)', type='password')
                role = st.selectbox('Role', Vault.ROLES, index=1)
                st.caption('Deliver the initial password and authenticator enrollment details privately. No email is sent.')
                create = st.form_submit_button('Create account', type='primary')
            if create:
                secret = vault.create_user(token, username, password, role)
                st.success('Account created. Enroll the user’s authenticator now.')
                enrollment(secret, username)
                st.warning('This setup key is shown once. Save the enrollment details privately before leaving this page.')
        with policy:
            role_table()

    elif page == 'Audit trail':
        st.header('Audit trail')
        st.caption('Follow the decisions your vault makes. View and export the latest 1,000 recorded events.')
        logs = vault.logs(token)
        a, b, c = st.columns(3)
        a.metric('Events in view', len(logs))
        b.metric('Allowed actions', sum(r['outcome'] == 'allowed' for r in logs))
        c.metric('Denied actions', sum(r['outcome'] == 'denied' for r in logs))
        x, y, z = st.columns(3)
        actor = x.selectbox('Actor', ['Everyone'] + sorted({r['actor'] for r in logs}))
        outcome = y.selectbox('Outcome', ['All outcomes', 'allowed', 'denied'])
        action = z.selectbox('Action', ['All actions'] + sorted({r['action'] for r in logs}))
        filtered = [r for r in logs if (actor == 'Everyone' or r['actor'] == actor)
                    and (outcome == 'All outcomes' or r['outcome'] == outcome)
                    and (action == 'All actions' or r['action'] == action)]
        display = [dict(r, at=time_label(r['at'])) for r in filtered]
        st.dataframe(display, hide_index=True, width='stretch')
        st.download_button('Export filtered audit CSV', csv_export(display, ['id', 'at', 'actor', 'action', 'target', 'outcome']),
                           'cipher-vault-audit.csv', 'text/csv', icon=':material/download:')
        st.caption('A denied event is an access decision, not proof of an attack. Server operators can modify local audit records.')

    elif page == 'My account':
        st.header('My account')
        st.caption('Know where you are signed in. Keep control of your workspace access.')
        a, b, c = st.columns(3)
        a.metric('Username', user['username'])
        b.metric('Role', user['role'])
        c.metric('Sign-in protection', '2 factors')
        st.subheader('Your active sessions')
        sessions = vault.own_sessions(token)
        st.dataframe([{'Session': 'This session' if s['current'] else 'Another session',
                       'Reference': s['fingerprint'], 'Signed in': time_label(s['created']),
                       'Expires': time_label(s['expires'])} for s in sessions], hide_index=True, width='stretch')
        st.caption('Sessions expire 30 minutes after sign-in. Device names and IP addresses are not collected.')
        if st.button('Sign out all other sessions', disabled=len(sessions) <= 1, icon=':material/devices:'):
            count = vault.revoke_other_sessions(token)
            toast(f'{count} other sessions signed out.')
        st.subheader('Your recent activity')
        activity = [r for r in vault.activity(token, 1000) if r['actor'] == user['username']][:8]
        for event in activity:
            activity_item(event['action'], event['actor'], time_label(event['at']), event['outcome'])
        st.info('For a lost authenticator or account recovery, contact a workspace administrator. Keep your authenticator recovery material offline.')

    elif page == 'Security guide':
        st.header('Security center')
        st.caption('Understand the controls protecting this workspace, and what still depends on your deployment.')
        layers, permissions, operations = st.tabs(['Protection layers', 'Role permissions', 'Deployment & recovery'])
        with layers:
            protections()
            summary = vault.security_summary(token)
            st.subheader('Cryptographic identity')
            st.caption('RSA public-key fingerprint · SHA-256. Useful for comparing the same vault across backups or restarts.')
            st.code(summary['key_fingerprint'], language=None)
            st.markdown('''
| Control | Implementation |
|---|---|
| Account passwords | Salted bcrypt hashes; minimum 12 characters |
| Authenticator | TOTP; 30-second codes; replay rejected |
| Login protection | Five failed attempts trigger a five-minute account lockout |
| File encryption | A fresh AES-256-GCM key and nonce for every upload |
| Key protection | RSA-3072 OAEP/SHA-256; encrypted private key |
| Integrity | GCM authentication plus a SHA-256 content check |
| Sessions | Server-side authorization; fixed 30-minute expiry |
''')
        with permissions:
            role_table()
        with operations:
            st.warning('VPN access is a network control. This application does not detect or establish a VPN connection.')
            st.markdown('''
**Free demonstration:** Streamlit Community Cloud runs this interface, but local files and accounts can be lost when its filesystem is replaced. Use disposable documents.

**Durable hosting:** use Render with a paid persistent disk, or the supplied Docker deployment with a persistent volume. Moving to Render’s free tier does not make SQLite persistent.

**Full VPN deployment:** run Docker on a server with WireGuard, bind to the VPN interface, and verify that the app is unreachable over the public interface.

**Backups:** save the database and your master key separately. Never replace the master key without migrating data. Losing the key means losing access to encrypted files.

**Trust boundary:** server operators with the master key can decrypt files. Metadata is stored in plaintext; local audit records are not tamper-proof. This project is an educational prototype.
''')

except VaultError as exc:
    st.error(str(exc))

footer()
