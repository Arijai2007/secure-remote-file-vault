# Free demo deployment: Vercel website + Render API

The React website is built from `web/` on Vercel. The Python API runs from the repository root on Render. This is a new vault, independent of the older Streamlit demo.

Live website: https://ciphervault-steel.vercel.app/

## Render

- Source: `Arijai2007/secure-remote-file-vault`, branch `main`.
- Runtime: Python 3.13, selected by `.python-version`.
- Build: `pip install -r requirements-web.txt`.
- Start: `python -m uvicorn web_api:app --host 0.0.0.0 --port $PORT`.
- Health path: `/healthz`.
- Plan: Free; region: Singapore.
- Environment: `VAULT_DATA_DIR=/tmp/cipher-vault`, `VAULT_COOKIE_SECURE=1`, and two independently generated private values for `VAULT_MASTER_KEY` and `VAULT_BOOTSTRAP_TOKEN`.
- API origin: `https://ciphervault-api-dt6o.onrender.com`.

`deploy/render-api-free.yaml` records the configuration. The existing root `render.yaml` remains the optional paid Streamlit deployment; it is not used for this service.

## Vercel

- Import the existing repository, not a duplicate clone.
- Set Root Directory to `web`, Framework to Vite, Build to `npm run build`, and Output to `dist`.
- `web/vercel.json` proxies `/api/*` to the Render API and rewrites frontend page routes to the React entrypoint.
- No vault master key or bootstrap token belongs on Vercel or in a `VITE_*` variable. Secrets stay on Render.
- Requests use the frontend origin; no permissive cross-origin cookie/CORS configuration is needed. HttpOnly, Secure, SameSite=Strict cookies remain in use. API responses are marked `Cache-Control: no-store`.
- Update the exact API destination in `web/vercel.json` if the Render service is replaced or renamed.

## Verify

1. Render `/healthz` returns `{"status":"ok"}`; `/api/status` returns the vault initialization state.
2. Vercel `/api/status` returns the same JSON instead of the React HTML page.
3. Refresh `/signin` and `/app/vault` directly to verify SPA routing.
4. In the website, initialize the administrator using the private bootstrap token saved from Render, then enroll an authenticator.
5. Check MFA login, upload, verification and download; test an Employee and Guest separately.

Free Render services sleep when idle and lose local files/accounts when their instance is replaced. Use disposable demonstration data only. Keep the master key and bootstrap token privately; the latter is needed if an empty instance requires initialization again. This public deployment does not provide VPN-only access. Hosting behind WireGuard still requires the documented self-hosted environment.
