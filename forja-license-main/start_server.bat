@echo off
setlocal
cd /d %~dp0

if not exist venv\Scripts\activate (
  echo Venv nao encontrado. Rode install_deps.bat primeiro.
  pause
  exit /b 1
)

call venv\Scripts\activate

if "%DATABASE_URL%"=="" goto missing_env
if "%FORJA_PRIVATE_KEY_B64%"=="" goto missing_env
if "%ADMIN_TOKEN%"=="" goto missing_env

echo Iniciando servidor de licencas em http://0.0.0.0:8787 ...
python -m uvicorn license_server:app --host 0.0.0.0 --port 8787

pause
exit /b %ERRORLEVEL%

:missing_env
echo Configure DATABASE_URL, FORJA_PRIVATE_KEY_B64 e ADMIN_TOKEN no ambiente antes de iniciar.
exit /b 1
