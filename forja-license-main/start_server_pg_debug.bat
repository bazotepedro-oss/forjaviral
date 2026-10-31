@echo off
REM Debug starter: mostra erro real de import

cd /d %~dp0
echo [Forja] Pasta atual: %cd%
echo.

if not exist license_server.py (
  echo ERRO: license_server.py NAO encontrado nesta pasta.
  pause
  exit /b 1
)

if "%DATABASE_URL%"=="" goto missing_env
if "%FORJA_PRIVATE_KEY_B64%"=="" goto missing_env
if "%ADMIN_TOKEN%"=="" goto missing_env

echo Testando import do modulo...
python -c "import license_server; print('OK: import license_server')"
echo.
echo Iniciando servidor...
python -m uvicorn license_server:app --host 0.0.0.0 --port 8787
pause
exit /b %ERRORLEVEL%

:missing_env
echo Configure DATABASE_URL, FORJA_PRIVATE_KEY_B64 e ADMIN_TOKEN no ambiente antes de iniciar.
exit /b 1
