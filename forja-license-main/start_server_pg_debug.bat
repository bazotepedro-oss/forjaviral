@echo off
REM Debug starter: mostra erro real de import

cd /d %~dp0
echo [Forja] Pasta atual: %cd%
echo.

if not exist license_server_pg.py (
  echo ERRO: license_server_pg.py NAO encontrado nesta pasta.
  pause
  exit /b 1
)

REM ====== CONFIGURE AQUI ======
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/forja_license
set FORJA_PRIVATE_KEY_B64=REPLACE_ME_PRIVATE_KEY_B64
set ADMIN_TOKEN=FV291125
REM ============================

echo Testando import do modulo...
python diag_import_license_server_pg.py
echo.
echo Iniciando servidor...
python -m uvicorn license_server_pg:app --host 0.0.0.0 --port 8787
pause
