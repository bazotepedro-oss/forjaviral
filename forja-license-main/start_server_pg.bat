@echo off
REM Forja License PG - One-click install & run
REM Put this file in C:\forja-license (same folder as license_server.py)

cd /d %~dp0

echo ===============================
echo Forja License PG - START
echo Folder: %cd%
echo ===============================

REM --- Ensure venv exists ---
if not exist venv\Scripts\python.exe (
  echo Creating venv...
  python -m venv venv
)

call venv\Scripts\activate

echo Installing/Updating dependencies...
python -m pip install -U pip >nul
python -m pip install -r requirements_license_pg.txt

REM Secrets must be set in the process environment, never in this tracked file.
if "%DATABASE_URL%"=="" goto missing_env
if "%FORJA_PRIVATE_KEY_B64%"=="" goto missing_env
if "%ADMIN_TOKEN%"=="" goto missing_env

echo.
echo Testing import...
python -c "import license_server; print('OK: imported license_server')"

echo.
echo Starting server on port 8787...
python -m uvicorn license_server:app --host 0.0.0.0 --port 8787

pause
exit /b %ERRORLEVEL%

:missing_env
echo Configure DATABASE_URL, FORJA_PRIVATE_KEY_B64 e ADMIN_TOKEN no ambiente antes de iniciar.
exit /b 1
