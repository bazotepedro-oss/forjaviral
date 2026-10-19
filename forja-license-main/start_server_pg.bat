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

REM --- Set your env vars ---
REM IMPORTANT: change these if needed
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/forja_license
set FORJA_PRIVATE_KEY_B64=NVg0cD/7cM22nbn2ZOieQvFhIvKOg3o4vM39XUB+Xrs=
set ADMIN_TOKEN=FV291125

echo.
echo Testing import...
python -c "import license_server; print('OK: imported license_server')"

echo.
echo Starting server on port 8787...
python -m uvicorn license_server:app --host 0.0.0.0 --port 8787

pause
