"""Local, alert-only ML over audit metadata. No file contents leave the vault."""
from collections import defaultdict
import math
import random

from sklearn.ensemble import IsolationForest

FEATURES = ('failed_logins', 'denied_actions', 'downloads', 'download_bytes', 'distinct_files')
WINDOW = 300
MIN_TRAINING = 30


def activity_windows(events, now):
    groups = defaultdict(list)
    # Exclude the incomplete current window to avoid comparing partial and full windows.
    cutoff = int(now // WINDOW) * WINDOW
    for event in events:
        if event['action'] not in ('login', 'download', 'upload', 'delete', 'verify_integrity') and event['outcome'] != 'denied':
            continue
        start = int(event['at'] // WINDOW) * WINDOW
        if start >= cutoff:
            continue
        groups[(start, event['actor'])].append(event)
    windows = []
    for (start, actor), rows in sorted(groups.items()):
        downloads = [r for r in rows if r['action'] == 'download' and r['outcome'] == 'allowed']
        windows.append({'start': start, 'actor': actor,
                        'failed_logins': sum(r['action'] == 'login' and r['outcome'] == 'denied' for r in rows),
                        'denied_actions': sum(r['outcome'] == 'denied' for r in rows),
                        'downloads': len(downloads),
                        'download_bytes': sum(r.get('bytes_count', 0) for r in downloads),
                        'distinct_files': len({r['target'] for r in rows if r['action'] in ('download', 'upload', 'delete', 'verify_integrity') and r['outcome'] == 'allowed'})})
    return windows


def score_windows(training, evaluation):
    """Train on earlier windows; negative decision scores indicate model outliers."""
    vector = lambda row: [math.log1p(row[f]) for f in FEATURES]
    model = IsolationForest(n_estimators=150, contamination='auto', random_state=42, n_jobs=1)
    model.fit([vector(row) for row in training])
    medians = {f: sorted(r[f] for r in training)[len(training) // 2] for f in FEATURES}
    results = []
    for row, score in zip(evaluation, model.decision_function([vector(r) for r in evaluation])):
        signals = [f'{f.replace("_", " ")}: {row[f]} (baseline median {medians[f]})'
                   for f in FEATURES if row[f] > medians[f]]
        results.append(dict(row, decision_score=round(float(score), 6), anomalous=bool(score < 0),
                            signals='; '.join(signals) or 'No feature exceeds its baseline median'))
    return results


def analyze_activity(events, now):
    windows = activity_windows(events, now)
    # Split by time, keeping every actor in a time bucket on the same side.
    times = sorted({r['start'] for r in windows})
    split = times[min(len(times) - 1, int(len(times) * .8))] if times else 0
    training = [r for r in windows if r['start'] < split]
    evaluation = [r for r in windows if r['start'] >= split]
    if len(training) < MIN_TRAINING or len({tuple(r[f] for f in FEATURES) for r in training}) < 3:
        return {'ready': False, 'training_windows': len(training), 'results': [],
                'message': 'Collect at least 30 varied baseline user windows across multiple completed five-minute periods. Use the isolated synthetic demo while the vault is new.'}
    return {'ready': True, 'training_windows': len(training), 'results': score_windows(training, evaluation),
            'message': 'Earlier 80% of time buckets train the model; the remaining buckets are evaluated. Current incomplete bucket excluded. Alerts are not proof of attacks.'}


def synthetic_demo():
    """Reproducible classroom examples, never inserted into the real audit database."""
    rng = random.Random(42)
    training = []
    for i in range(150):
        n = rng.randint(1, 5)
        training.append(dict(start=i * WINDOW, actor='synthetic-baseline', failed_logins=0,
                             denied_actions=0, downloads=n, download_bytes=n * rng.randint(1000, 50000), distinct_files=n))
    evaluation = [dict(start=151 * WINDOW, actor='synthetic-normal', failed_logins=0, denied_actions=0,
                       downloads=3, download_bytes=75000, distinct_files=3),
                  dict(start=152 * WINDOW, actor='synthetic-download-burst', failed_logins=0, denied_actions=0,
                       downloads=150, download_bytes=150000000, distinct_files=100),
                  dict(start=153 * WINDOW, actor='synthetic-login-failures', failed_logins=40, denied_actions=40,
                       downloads=0, download_bytes=0, distinct_files=0)]
    return score_windows(training, evaluation)
