@echo off
setlocal
cd /d %~dp0

if not exist venv\Scripts\activate (
  echo Venv nao encontrado. Rode install_deps.bat primeiro.
  pause
  exit /b 1
)

call venv\Scripts\activate

REM ====== CONFIG ======
REM Cole aqui sua PRIVATE_KEY_B64 (seed 32 bytes em base64) e um ADMIN_TOKEN forte.
REM Gere usando: python generate_keys.py
set FORJA_PRIVATE_KEY_B64=sPUrti+8k0Bj8fElkzDuLXDRhriWTf9HraHHEIrsgQk=
set ADMIN_TOKEN=FV291125
REM ====================

echo Iniciando servidor de licencas em http://0.0.0.0:8787 ...
python -m uvicorn license_server:app --host 0.0.0.0 --port 8787

pause
