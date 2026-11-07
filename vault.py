"""Security and persistence boundary. UI code never authorizes operations."""
import hashlib
import hmac
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import bcrypt
import pyotp
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class VaultError(Exception):
    pass


class Vault:
    MAX_FILE = 20 * 1024 * 1024
    ROLES = ('Admin', 'Employee', 'Guest')

    def __init__(self, directory, master_key):
        if len(master_key.encode()) < 32:
            raise VaultError('VAULT_MASTER_KEY must contain at least 32 characters.')
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / 'vault.sqlite3'
        self.key = hashlib.sha256(master_key.encode()).digest()
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password BLOB NOT NULL,
              role TEXT NOT NULL, totp BLOB NOT NULL, last_step INTEGER NOT NULL DEFAULT -1,
              active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS sessions (
              token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts (
              username TEXT PRIMARY KEY, failures INTEGER NOT NULL, until REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS files (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT NOT NULL,
              shared INTEGER NOT NULL, size INTEGER NOT NULL, created REAL NOT NULL,
              digest TEXT NOT NULL, wrapped BLOB NOT NULL, nonce BLOB NOT NULL, data BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
              actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL,
              outcome TEXT NOT NULL);
            ''')
            row = db.execute("SELECT value FROM settings WHERE name='rsa'").fetchone()
            if row is None:
                private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
                pem = private.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.BestAvailableEncryption(self.key))
                db.execute("INSERT OR IGNORE INTO settings VALUES ('rsa', ?)", (pem,))
                row = db.execute("SELECT value FROM settings WHERE name='rsa'").fetchone()
            try:
                self.private = serialization.load_pem_private_key(row['value'], self.key)
            except ValueError as exc:
                raise VaultError('The master key does not unlock this vault. Restore the original key.') from exc

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def seal(self, value):
        nonce = secrets.token_bytes(12)
        return nonce + AESGCM(self.key).encrypt(nonce, value.encode(), b'totp-v1')

    def unseal(self, value):
        return AESGCM(self.key).decrypt(value[:12], value[12:], b'totp-v1').decode()

    @staticmethod
    def password_hash(password):
        if len(password) < 12 or len(password.encode()) > 72:
            raise VaultError('Use a password of at least 12 characters and at most 72 UTF-8 bytes.')
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

    @staticmethod
    def audit(db, actor, action, target='', outcome='allowed'):
        db.execute('INSERT INTO audit(at,actor,action,target,outcome) VALUES(?,?,?,?,?)',
                   (time.time(), actor, action, str(target)[:160], outcome))

    def is_empty(self):
        with self.db() as db:
            return db.execute('SELECT count(*) FROM users').fetchone()[0] == 0

    def bootstrap(self, username, password, secret, code):
        if not pyotp.TOTP(secret).verify(code, valid_window=0):
            raise VaultError('Authenticator code is invalid. Check the device clock.')
        hashed = self.password_hash(password)
        username = self.normalize_name(username)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM users').fetchone()[0]:
                raise VaultError('Vault is already initialized.')
            db.execute('INSERT INTO users(id,username,password,role,totp) VALUES(?,?,?,?,?)',
                       (uuid.uuid4().hex, username, hashed, 'Admin', self.seal(secret)))
            self.audit(db, username, 'initialize')

    @staticmethod
    def normalize_name(username):
        username = username.strip().lower()
        if not 3 <= len(username) <= 64 or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789._-@' for c in username):
            raise VaultError('Username must be 3–64 letters, numbers, or . _ - @.')
        return username

    def login(self, username, password, code, now=None):
        now = time.time() if now is None else now
        username = username.strip().lower()[:64]
        error = None
        token = None
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            attempt = db.execute('SELECT * FROM attempts WHERE username=?', (username,)).fetchone()
            user = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            if attempt and attempt['until'] > now:
                error = 'Too many attempts. Wait 5 minutes before trying again.'
            else:
                # Always perform the expensive password check, including unknown accounts.
                dummy = b'$2b$12$LQv3c1yqBWVHxkd0LHAkCOY.Hf1qx7v4LjWw90yS0a3R2ZvyZaA2K'
                candidate = password.encode()[:72]
                valid_pw = bcrypt.checkpw(candidate, user['password'] if user else dummy)
                step = int(now // 30)
                valid_otp = bool(user and pyotp.TOTP(self.unseal(user['totp'])).verify(code, for_time=now, valid_window=0))
                if not (user and user['active'] and valid_pw and len(password.encode()) <= 72 and valid_otp and step > user['last_step']):
                    count = (attempt['failures'] if attempt and now < attempt['until'] + 300 else 0) + 1
                    db.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)',
                               (username, count, now + 300 if count >= 5 else now))
                    error = 'Invalid credentials, inactive account, or already-used code.'
                else:
                    db.execute('UPDATE users SET last_step=? WHERE id=?', (step, user['id']))
                    db.execute('DELETE FROM attempts WHERE username=?', (username,))
                    db.execute('DELETE FROM sessions WHERE expires<?', (now,))
                    token = secrets.token_urlsafe(32)
                    db.execute('INSERT INTO sessions VALUES(?,?,?)', (self.token_hash(token), user['id'], now + 1800))
            self.audit(db, username, 'login', outcome='denied' if error else 'allowed')
        if error:
            raise VaultError(error)
        return token

    @staticmethod
    def token_hash(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def user(self, token):
        with self.db() as db:
            row = db.execute('SELECT u.id,u.username,u.role FROM users u JOIN sessions s ON s.user_id=u.id '
                             'WHERE s.token=? AND s.expires>? AND u.active=1',
                             (self.token_hash(token), time.time())).fetchone()
            if row is None:
                raise VaultError('Session expired. Sign in again.')
            return dict(row)

    def require(self, token, roles, action, target=''):
        user = self.user(token)
        if user['role'] not in roles:
            with self.db() as db:
                self.audit(db, user['username'], action, target, 'denied')
            raise VaultError('Your role does not permit this action.')
        return user

    def logout(self, token):
        user = self.user(token)
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE token=?', (self.token_hash(token),))
            self.audit(db, user['username'], 'logout')

    def create_user(self, token, username, password, role):
        actor = self.require(token, ('Admin',), 'create_user', username)
        username = self.normalize_name(username)
        if role not in self.ROLES:
            raise VaultError('Unknown role.')
        secret = pyotp.random_base32()
        hashed = self.password_hash(password)
        with self.db() as db:
            try:
                db.execute('INSERT INTO users(id,username,password,role,totp) VALUES(?,?,?,?,?)',
                           (uuid.uuid4().hex, username, hashed, role, self.seal(secret)))
            except sqlite3.IntegrityError as exc:
                raise VaultError('Username already exists.') from exc
            self.audit(db, actor['username'], 'create_user', username)
        return secret

    def users(self, token):
        self.require(token, ('Admin',), 'list_users')
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT id,username,role,active FROM users ORDER BY username')]

    def set_active(self, token, user_id, active):
        actor = self.require(token, ('Admin',), 'set_active', user_id)
        if actor['id'] == user_id:
            raise VaultError('You cannot deactivate your own account.')
        with self.db() as db:
            db.execute('UPDATE users SET active=? WHERE id=?', (int(active), user_id))
            db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
            self.audit(db, actor['username'], 'activate' if active else 'deactivate', user_id)

    def files(self, token):
        user = self.user(token)
        with self.db() as db:
            rows = db.execute('SELECT f.id,f.name,f.owner,u.username AS uploaded_by,f.shared,f.size,f.created,f.digest '
                              'FROM files f JOIN users u ON u.id=f.owner '
                              'WHERE ?=\'Admin\' OR f.owner=? OR f.shared=1 ORDER BY f.created DESC',
                              (user['role'], user['id'])).fetchall()
            self.audit(db, user['username'], 'list_files')
            return [dict(r) for r in rows]

    def upload(self, token, name, data, shared=False):
        user = self.require(token, ('Admin', 'Employee'), 'upload', name)
        if not data or len(data) > self.MAX_FILE:
            raise VaultError('Upload a nonempty file of at most 20 MiB.')
        name = name.replace('\\', '/').split('/')[-1].strip()
        if not name or len(name) > 200 or any(ord(c) < 32 for c in name):
            raise VaultError('Invalid filename.')
        file_id = uuid.uuid4().hex
        nonce = secrets.token_bytes(12)
        key = AESGCM.generate_key(bit_length=256)
        digest = hashlib.sha256(data).hexdigest()
        encrypted = AESGCM(key).encrypt(nonce, data, file_id.encode())
        wrapped = self.private.public_key().encrypt(key, padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        with self.db() as db:
            db.execute('INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (file_id, name, user['id'], int(shared), len(data), time.time(), digest, wrapped, nonce, encrypted))
            self.audit(db, user['username'], 'upload', file_id)
        return file_id

    def download(self, token, file_id):
        return self._read_file(token, file_id, 'download')

    def _read_file(self, token, file_id, action):
        user = self.require(token, ('Admin', 'Employee'), action, file_id)
        error = None
        result = None
        with self.db() as db:
            row = db.execute('SELECT * FROM files WHERE id=?', (file_id,)).fetchone()
            if row is None or not (user['role'] == 'Admin' or row['owner'] == user['id'] or row['shared']):
                error = 'File unavailable or access denied.'
            else:
                try:
                    key = self.private.decrypt(row['wrapped'], padding.OAEP(
                        mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
                    data = AESGCM(key).decrypt(row['nonce'], row['data'], file_id.encode())
                    if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), row['digest']):
                        raise ValueError('Hash mismatch')
                    result = (row['name'], data)
                except (ValueError, InvalidTag):
                    error = 'Integrity verification failed. Download blocked.'
            self.audit(db, user['username'], action, file_id, 'denied' if error else 'allowed')
        if error:
            raise VaultError(error)
        return result

    def delete(self, token, file_id):
        user = self.require(token, ('Admin',), 'delete', file_id)
        with self.db() as db:
            db.execute('DELETE FROM files WHERE id=?', (file_id,))
            self.audit(db, user['username'], 'delete', file_id)

    def set_shared(self, token, file_id, shared):
        user = self.require(token, ('Admin', 'Employee'), 'change_sharing', file_id)
        error = None
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT owner FROM files WHERE id=?', (file_id,)).fetchone()
            if row is None or (user['role'] != 'Admin' and row['owner'] != user['id']):
                error = 'Only the owner or an administrator can change sharing.'
            else:
                db.execute('UPDATE files SET shared=? WHERE id=?', (int(bool(shared)), file_id))
            self.audit(db, user['username'], 'share_file' if shared else 'unshare_file',
                       file_id, 'denied' if error else 'allowed')
        if error:
            raise VaultError(error)

    def verify(self, token, file_id):
        # Verification uses the same decryption and authorization path as download,
        # but returns no plaintext to the caller.
        name, data = self._read_file(token, file_id, 'verify_integrity')
        return {'name': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def activity(self, token, limit=30):
        user = self.user(token)
        limit = max(1, min(int(limit), 1000))
        with self.db() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM audit WHERE ?='Admin' OR actor=? ORDER BY id DESC LIMIT ?",
                (user['role'], user['username'], limit))]

    def security_summary(self, token):
        user = self.user(token)
        with self.db() as db:
            now = time.time()
            denied = db.execute("SELECT count(*) FROM audit WHERE at>? AND outcome='denied' "
                                "AND (?='Admin' OR actor=?)", (now - 86400, user['role'], user['username'])).fetchone()[0]
            sessions = db.execute('SELECT count(*) FROM sessions s JOIN users u ON s.user_id=u.id '
                                  "WHERE s.expires>? AND u.active=1 AND (?='Admin' OR u.id=?)",
                                  (now, user['role'], user['id'])).fetchone()[0]
            expiry = db.execute('SELECT expires FROM sessions WHERE token=?', (self.token_hash(token),)).fetchone()[0]
        public = self.private.public_key().public_bytes(serialization.Encoding.DER,
                                                       serialization.PublicFormat.SubjectPublicKeyInfo)
        return {'denied_24h': denied, 'active_sessions': sessions, 'expires': expiry,
                'key_fingerprint': hashlib.sha256(public).hexdigest()}

    def own_sessions(self, token):
        user = self.user(token)
        current = self.token_hash(token)
        with self.db() as db:
            rows = db.execute('SELECT token,expires FROM sessions WHERE user_id=? AND expires>? ORDER BY expires DESC',
                              (user['id'], time.time())).fetchall()
        return [{'fingerprint': r['token'][:12], 'created': r['expires'] - 1800,
                 'expires': r['expires'], 'current': r['token'] == current} for r in rows]

    def revoke_other_sessions(self, token):
        user = self.user(token)
        with self.db() as db:
            cursor = db.execute('DELETE FROM sessions WHERE user_id=? AND token!=?',
                                (user['id'], self.token_hash(token)))
            count = cursor.rowcount
            self.audit(db, user['username'], 'revoke_other_sessions', str(count))
        return count

    def logs(self, token):
        user = self.require(token, ('Admin',), 'view_audit')
        with self.db() as db:
            self.audit(db, user['username'], 'view_audit')
            return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 1000')]
