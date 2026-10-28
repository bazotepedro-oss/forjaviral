@echo off
title FABRICA DOS CORTES - SERVIDOR LOCALHOST (NETFLIX)
chcp 65001 >nul
cls

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
echo  CREDENCIAIS DE TESTE:
echo    Admin: admin@fabricadecortes.com   ^| Senha: admin123
echo    Aluno: aluno@teste.com             ^| Senha: admin123
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

:: Abre o navegador automaticamente após 1.5 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080/index.php"

:: Inicia o servidor PHP com php.ini configurado
"%RUN_PHP%" -c php.ini -S 127.0.0.1:8080

pause
