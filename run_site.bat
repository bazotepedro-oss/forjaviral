@echo off
setlocal
title Forja Viral - Site Localhost

cd /d "%~dp0site"
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Microsoft\VisualStudio\NodeJs;%PATH%"

echo ============================================
echo   Iniciando Forja Viral Site em Localhost
echo ============================================
echo.
echo Servidor: http://localhost:3000
echo.

start "" "http://localhost:3000"
node node_modules\next\dist\bin\next dev -p 3000

pause
