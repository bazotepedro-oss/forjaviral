FORJA LICENSE (POSTGRES + CREDITOS)

Arquivos principais:
- license_server_pg.py  -> servidor FastAPI + Postgres + /consume + painel /admin
- start_server_pg.bat   -> inicia o servidor (configure as 3 vars)
- requirements_license_pg.txt

Como rodar (local):
1) pip install -r requirements_license_pg.txt
2) Edite start_server_pg.bat e cole:
   - DATABASE_URL (sua senha do postgres)
   - FORJA_PRIVATE_KEY_B64 (private seed base64)
   - ADMIN_TOKEN
3) Execute start_server_pg.bat

Testes:
- http://127.0.0.1:8787/health
- http://127.0.0.1:8787/admin?token=SEU_TOKEN
