@echo off
title Atualizar Fabrica de Cortes
cd /d "%~dp0"
echo ==============================================================
echo        FABRICA DE CORTES - ATUALIZADOR OFICIAL
echo ==============================================================
echo.
echo Baixando versao mais recente diretamente do GitHub oficial...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $z='%~dp0temp_update.zip'; Invoke-WebRequest -Uri 'https://codeload.github.com/bazotepedro-oss/forjaviral/zip/refs/heads/main' -OutFile $z; Expand-Archive $z -DestinationPath '%~dp0temp_extract' -Force; Get-ChildItem '%~dp0temp_extract\forjaviral-main\*' | Where-Object { $_.Name -notin @('.venv', 'VIRALS', 'models', 'KEY.txt', 'api_config.json', 'site') } | Copy-Item -Destination '%~dp0' -Recurse -Force; Remove-Item $z -Force -ErrorAction SilentlyContinue; Remove-Item '%~dp0temp_extract' -Recurse -Force -ErrorAction SilentlyContinue"
echo.
echo ==============================================================
echo  [OK] Sistema atualizado com sucesso para a versao mais recente!
echo  Suas configuracoes, chaves e videos foram preservados.
echo ==============================================================
echo.
pause

