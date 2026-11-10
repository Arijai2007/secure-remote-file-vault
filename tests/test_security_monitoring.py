import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from test_vault import account, env
from vault import Vault, VaultError
from security_analytics import activity_windows, analyze_activity, synthetic_demo


def test_audit_restart_checkpoint_and_transfer_sizes(env):
    vault, admin, _ = env
    fid = vault.upload(admin, 'report.txt', b'hello')
    vault.download(admin, fid)
    checkpoint = vault.audit_checkpoint(admin)
    vault.files(admin)
    reopened = Vault(vault.root, 'a-test-master-key-with-more-than-32-characters')
    assert reopened.verify_audit(admin, checkpoint)['valid']
    with vault.db() as db:
        assert db.execute("SELECT bytes_count FROM audit_seals s JOIN audit a ON a.id=s.event_id WHERE a.action='download'").fetchone()[0] == 5
    checkpoint['mac'] = '0' * 64
    with pytest.raises(VaultError, match='signature'):
        vault.verify_audit(admin, checkpoint)


@pytest.mark.parametrize('change', [
    "UPDATE audit SET actor='intruder' WHERE id=1",
    'DELETE FROM audit WHERE id=1',
    'DELETE FROM audit WHERE id=(SELECT max(id) FROM audit)',
    'DELETE FROM audit',
    "INSERT INTO audit(at,actor,action,target,outcome) VALUES(0,'x','x','','allowed')",
    'UPDATE audit_seals SET bytes_count=999 WHERE event_id=1',
    "UPDATE settings SET value='invalid-json' WHERE name='audit_head_v1'",
])
def test_audit_detects_tampering(env, change):
    vault, admin, _ = env
    with vault.db() as db:
        db.execute(change)
    assert not vault.verify_audit(admin)['valid']
    with pytest.raises(VaultError, match='integrity'):
        vault.anomaly_report(admin)
    with pytest.raises(VaultError, match='damaged'):
        vault.audit_checkpoint(admin)


def test_trusted_checkpoint_detects_full_database_rollback(env):
    vault, admin, _ = env
    snapshot = vault.db_path.read_bytes()
    vault.files(admin)
    checkpoint = vault.audit_checkpoint(admin)
    vault.db_path.write_bytes(snapshot)
    assert vault.verify_audit(admin)['valid']  # Internally consistent old snapshot.
    assert not vault.verify_audit(admin, checkpoint)['valid']


def test_legacy_migration_preserves_rows_and_is_idempotent(env):
    vault, admin, _ = env
    with vault.db() as db:
        old = [dict(r) for r in db.execute('SELECT * FROM audit')]
        db.execute('DROP TABLE audit_seals')
        db.execute("DELETE FROM settings WHERE name='audit_head_v1'")
    reopened = Vault(vault.root, 'a-test-master-key-with-more-than-32-characters')
    status = reopened.verify_audit(admin)
    assert status['valid'] and status['legacy_through'] == old[-1]['id']
    with reopened.db() as db:
        assert [dict(r) for r in db.execute('SELECT * FROM audit')] == old
    assert Vault(vault.root, 'a-test-master-key-with-more-than-32-characters').verify_audit(admin)['valid']


def test_concurrent_audit_writers(env):
    vault, admin, _ = env
    def write(i):
        with vault.db() as db:
            vault.audit(db, 'admin', 'concurrent', str(i))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(16)))
    assert vault.verify_audit(admin)['valid']


def test_monitoring_and_integrity_are_admin_only(env):
    vault, admin, _ = env
    for role in ('Employee', 'Guest'):
        token = account(vault, admin, role.lower(), role)
        for action in (vault.verify_audit, vault.audit_checkpoint, vault.anomaly_report):
            with pytest.raises(VaultError):
                action(token)
    assert not vault.anomaly_report(admin)['ready']
    assert vault.verify_audit(admin)['valid']


def test_synthetic_ai_detects_bursts_without_flagging_normal_example():
    results = synthetic_demo()
    assert not results[0]['anomalous']
    assert results[1]['anomalous'] and results[2]['anomalous']
    assert results == synthetic_demo()


def test_window_features_ignore_incomplete_bucket_and_count_bytes():
    events = [dict(at=301, actor='alice', action='download', outcome='allowed', target='file1', bytes_count=123),
              dict(at=302, actor='alice', action='download', outcome='denied', target='private', bytes_count=0),
              dict(at=601, actor='alice', action='login', outcome='denied', target='', bytes_count=0)]
    rows = activity_windows(events, now=650)
    assert len(rows) == 1
    assert rows[0]['downloads'] == 1 and rows[0]['download_bytes'] == 123
    assert rows[0]['distinct_files'] == 1 and rows[0]['denied_actions'] == 1


def test_real_analysis_uses_earlier_time_buckets_only():
    events = []
    for i in range(50):
        for j in range(1 + i % 4):
            events.append(dict(at=i * 300 + 1, actor='alice', action='download', outcome='allowed',
                               target=str(j), bytes_count=1000 + i))
    report = analyze_activity(events, now=51 * 300)
    assert report['ready'] and report['training_windows'] == 40
    assert len(report['results']) == 10
    assert min(r['start'] for r in report['results']) == 40 * 300


@pytest.mark.parametrize('checkpoint', [[], {'id': -1, 'mac': 'x', 'signature': 'x'},
                                      {'id': 1, 'mac': '0' * 64, 'signature': '\u2603' * 64}])
def test_invalid_checkpoint_is_rejected(env, checkpoint):
    vault, admin, _ = env
    with pytest.raises(VaultError, match='checkpoint'):
        vault.verify_audit(admin, checkpoint)
