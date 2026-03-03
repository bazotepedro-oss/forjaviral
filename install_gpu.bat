@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ===============================
echo Forja Viral - Install (GPU)
echo ===============================

REM Create venv
if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate

python -m pip install --upgrade pip

echo Installing Torch GPU (cu121)...
pip install torch==2.3.1+cu121 torchaudio==2.3.1+cu121 --index-url https://download.pytorch.org/whl/cu121

echo Installing common requirements (locked)...
pip install -r requirements_common.txt -c constraints.txt

echo Done.
pause
