Railway Deploy (no-cost reality check)
- Railway Free plan: 30-day trial with $5 credit, then Free plan with $1 credit/month. citeturn0search8turn0search2
- If you enable Serverless/App Sleeping, service can sleep after inactivity and wake on first request. citeturn0search1turn0search3

This folder is a minimal Docker deploy for the license server.
1) Create a Railway project -> New Service -> Deploy from Dockerfile.
2) Add a PostgreSQL plugin, copy DATABASE_URL into service vars.
3) Add env vars:
   - FORJA_PRIVATE_KEY_B64
   - ADMIN_TOKEN
   - APP_ID (optional)
4) Expose port: Railway sets PORT; server binds to it automatically.

Notes:
- Free credits may be insufficient for always-on. Expect sleeping/cold-start unless you pay. citeturn0search8turn0search0
