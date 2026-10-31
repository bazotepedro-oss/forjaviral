@echo off
title FABRICA DOS CORTES - SERVIDOR LOCALHOST (NETFLIX)
chcp 65001 >nul
cls
cd /d "%~dp0"

set "APP_ENV=development"
set "MEMBERS_SQLITE_PATH=%TEMP%\fabricadecortes-members-local.sqlite"

echo ====================================================================
echo   FÁBRICA DOS CORTES - PLATAFORMA DE MEMBROS (ESTILO NETFLIX)
echo ====================================================================
echo.
echo  Iniciando servidor local PHP...
echo.
echo  ● URL da Plataforma : http://localhost:8080/index.php
echo  ● Painel Admin      : http://localhost:8080/admin.php
echo.
echo  ------------------------------------------------------------------
echo  Nao ha senhas padrao. Em uma base local nova, sera criada uma senha temporaria aleatoria.
echo  ------------------------------------------------------------------
echo.
echo  Pressione CTRL+C para encerrar o servidor quando terminar.
echo ====================================================================
echo.

set "PHP_EXE=C:\Users\bazot\AppData\Local\Microsoft\WinGet\Packages\PHP.PHP.8.3_Microsoft.Winget.Source_8wekyb3d8bbwe\php.exe"

if exist "%PHP_EXE%" (
    set "RUN_PHP=%PHP_EXE%"
) else (
    set "RUN_PHP=php"
)

if not exist "%MEMBERS_SQLITE_PATH%" (
    echo Criando base local de desenvolvimento e primeiro administrador...
    "%RUN_PHP%" create_admin.php admin@localhost.test
    if errorlevel 1 exit /b 1
)

:: Abre o navegador automaticamente após 1.5 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080/index.php"

:: Inicia o servidor PHP com php.ini configurado
"%RUN_PHP%" -c php.ini -S 127.0.0.1:8080

pause
