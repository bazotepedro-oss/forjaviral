@echo off
setlocal

echo ===============================
echo Forja Viral - Auto Install
echo ===============================

nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  echo NVIDIA detected. Installing GPU version...
  call install_gpu.bat
) else (
  echo No NVIDIA detected. Installing CPU version...
  call install_cpu.bat
)

endlocal
