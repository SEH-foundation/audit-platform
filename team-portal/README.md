# SEH Connectors Portal

Internal team portal for MCP connectors and usage instructions.

## Deploy on Vercel

1) Create a new Vercel project and select `audit-platform/team-portal`.
2) Set environment variables from `.env.example`.
3) Deploy.

## Environment Variables

- `NEXTAUTH_URL` - Vercel URL (e.g. `https://seh-connectors.vercel.app`)
- `NEXTAUTH_SECRET` - random secret
- `GOOGLE_CLIENT_ID` - Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth Client Secret
- `ALLOWED_EMAIL_DOMAIN` - `seh.foundation`

## Updating Connectors

Edit `team-portal/data/connectors.json` and redeploy.

## Downloads (S3/R2)

Add a `download_url` field per connector in `team-portal/data/connectors.json`.
Point it to your S3/R2 public URL (e.g. `https://downloads.seh.foundation/...`).

## Tools Catalog

Tool sets are stored in `team-portal/data/tools.json` and rendered per connector.

## Status Page

Visit `/status` to see live health checks for each connector.

## Local Dev

```bash
cd team-portal
npm install
npm run dev
```
