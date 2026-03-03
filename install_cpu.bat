@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ===============================
echo Forja Viral - Install (CPU)
echo ===============================

REM Create venv
if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate

python -m pip install --upgrade pip

echo Installing Torch CPU...
pip install torch==2.3.1+cpu torchaudio==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu

echo Installing common requirements (locked)...
pip install -r requirements_common.txt -c constraints.txt

echo Done.
pause
