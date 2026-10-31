@echo off
setlocal
cd /d %~dp0

if not exist venv (
  echo [1/3] Criando venv...
  python -m venv venv
)

echo [2/3] Ativando venv...
call venv\Scripts\activate

echo [3/3] Instalando dependencias...
python -m pip install -U pip
pip install -r requirements.txt

echo.
echo OK. Agora rode start_server.bat
pause
