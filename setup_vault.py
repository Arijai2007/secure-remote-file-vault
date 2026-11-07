"""Generate deployment secrets, or write an ignored local secret file."""
import argparse
import secrets
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--generate-secrets', action='store_true')
parser.add_argument('--local', action='store_true')
args = parser.parse_args()
text = f'VAULT_MASTER_KEY = "{secrets.token_urlsafe(48)}"\nVAULT_BOOTSTRAP_TOKEN = "{secrets.token_urlsafe(32)}"\n'
if args.local:
    target = Path('.streamlit/secrets.toml')
    target.parent.mkdir(exist_ok=True)
    with target.open('x', encoding='utf-8') as output:
        output.write(text)
    print('Created .streamlit/secrets.toml. Keep it private; back it up before storing files.')
elif args.generate_secrets:
    print(text)
else:
    parser.print_help()
