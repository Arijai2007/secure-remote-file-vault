# Deployment and demonstration

## Choose a host

| Host | Fit for this implementation |
|---|---|
| Streamlit Community Cloud | Easy free demonstration; local files/accounts are not durable |
| Render with a paid persistent disk | Good match for this single-instance Python/SQLite app with durable storage |
| Render free service | Demonstration only; local files are lost on restart/redeploy/spindown |
| Vercel | Better for a separately designed frontend/API with external durable storage; this app currently runs as a Streamlit server |
| VPS + Docker + WireGuard | Best way to demonstrate the synopsis's complete VPN-only network layer |

Streamlit is the UI framework; Community Cloud and Render are hosting choices. You can run the same Streamlit UI on Render or a VPS without rewriting it.

Sources: [Render persistent disks](https://render.com/docs/disks), [Render free service limits](https://render.com/docs/free), [Streamlit local storage](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data), [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python).

## Render with persistent storage (optional paid deployment)

The repository includes `render.yaml`. Create a Blueprint in Render from this repository, inspect the proposed compute and disk costs, and then deploy if you choose to pay for this hosting. The Blueprint selects the `0.5c-512mb` paid compute plan, a 1 GB disk mounted at `/var/data`, Python 3.13, generated secrets, and a Streamlit health check. No Render service is created simply by committing this file.

The app writes its SQLite database and encrypted file contents to `/var/data/cipher-vault`. After deployment, retrieve the bootstrap token from your service's environment settings and initialize your administrator in the app. Securely back up the generated master key. Do not regenerate it after storing data.

This creates a **new** empty vault. Existing Community Cloud accounts/files are not migrated automatically. Migrating an existing vault requires a consistent database backup and the exact original master key; do not copy a new generated key over an existing database. Keep one running instance with this SQLite/disk design. Render handles HTTPS, but a public Render URL does not add the VPN layer.

## Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ using the GitHub account that owns this repository.
2. Create an app from `Arijai2007/secure-remote-file-vault`, branch `main`, entrypoint `app.py`.
3. Choose a supported Python version (tested with Python 3.13).
4. Run `python setup_vault.py --generate-secrets` privately. Paste its TOML output into **Advanced settings → Secrets**. Save a secure backup. Do not put secrets in GitHub.
5. Deploy. Open the app, enter your bootstrap token, create the administrator, scan the authenticator QR and enter its code. Remove the bootstrap token from host secrets after initialization if desired; reinitialization is still blocked by the database.
6. Use the administrator to create Employee and Guest accounts and deliver their initial passwords and authenticator setup details privately.

**Cloud restrictions:** local SQLite storage can disappear when the app is rebuilt/restarted/replaced. Keep only disposable demonstration files here. The application is reachable over the internet; password/TOTP protects access but this is not a VPN-only deployment. Private repository or host access controls are separate from application roles. A live login page is not evidence of VPN protection.

## Docker with persistent storage

Copy `.env.example` to `.env` and replace both secrets with independently generated random values. Use `python setup_vault.py --generate-secrets` to obtain values; the output is TOML, whereas `.env` should contain unquoted `NAME=value` entries.

```sh
docker compose up -d --build
docker compose ps
```

By default the host listens on `127.0.0.1:8501`, not every public network interface. Named volume `vault-data` holds the database and encrypted RSA private key across container replacements. Back up the volume consistently (stop the app or use SQLite's backup API), plus a separate offline copy of the master key. Do not delete the volume when restarting.

## VPN layer with WireGuard

Provision WireGuard on a Linux server using the official distribution packages and https://www.wireguard.com/quickstart/. Keep the private keys off GitHub and create a unique peer/key for every device. Example address plan: server `10.8.0.1/24`, one client `10.8.0.2/32`. Configure a UDP endpoint and firewall rule for the WireGuard port (typically 51820). Configure client `AllowedIPs = 10.8.0.1/32` for only this service.

After the VPN interface is up, set `VAULT_BIND_IP=10.8.0.1` in `.env` and recreate the app container. Reach the app at `http://10.8.0.1:8501` while connected through WireGuard. Use a TLS reverse proxy and secure WebSocket forwarding for a stronger deployment. Verify externally that public TCP 8501 is unreachable. Docker can bypass some host firewall arrangements; binding to the explicit VPN address is necessary, and the effective host/provider rules must also be checked. Do not forward public TCP 8501.

Starter configuration templates are in `deploy/wireguard/`. Replace every placeholder. Generate each device's private/public key pair with WireGuard's `wg genkey` / `wg pubkey` tools locally, and exchange only public keys. These templates route only traffic to the vault server, so general internet forwarding/NAT is unnecessary. Start the server tunnel before the Docker container so that the bind address exists.

The repository does not claim to install or provision a VPN automatically: server keys, peer enrollment, network routing and firewall verification require the actual server environment.

## Presentation walkthrough

1. Show the VPN connection and verify the service is unreachable without it (self-hosted mode).
2. Try a wrong password/code; sign in with a correct unused authenticator code.
3. Create Employee and Guest accounts. Log in using separate browsers/sessions.
4. Upload a private file as Employee; a different employee and Guest cannot access it.
5. Upload a shared file: Employee can download, Guest sees metadata only.
6. Verify downloaded content matches the original and inspect its SHA-256 fingerprint.
7. Run the tamper-detection tests to show altered ciphertext is rejected.
8. Open the Admin audit dashboard to inspect allowed and denied actions.
9. Deactivate an account and demonstrate that its old session is rejected.

Never use real sensitive data in a classroom/cloud demonstration.
