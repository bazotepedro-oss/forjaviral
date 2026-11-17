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

ATENCAO: o HWID foi removido do servidor (versao 1.3.20).
Para valer em producao, este servico precisa ser redesployado no Railway.
Sem o redeploy, as chaves continuam presas ao primeiro computador.

Como publicar:
1) Railway -> projeto -> servico do servidor de licencas.
2) Opcao A: Deploy -> Redeploy (usa o ultimo codigo do repositorio).
   Opcao B: se o servico estiver ligado ao GitHub, basta um push na branch main.
3) Confirme com este teste (deve responder not_found, e nao missing_fields):

   curl -X POST https://forja-license-production.up.railway.app/api/license/check ^
     -H "content-type: application/json" ^
     -d "{"license_key":"FC-TESTE-INEXISTENTE"}"

