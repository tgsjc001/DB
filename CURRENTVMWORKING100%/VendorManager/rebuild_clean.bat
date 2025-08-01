@echo off
echo Killing VendorManager.exe if running...
taskkill /f /im VendorManager.exe >nul 2>&1

REM Wait up to 5 seconds to allow OS to fully release file handles
echo Waiting for process to exit...
timeout /t 5 >nul

echo Cleaning previous build files...
rmdir /s /q build
rmdir /s /q dist
for /r %%i in (__pycache__) do if exist "%%i" rmdir /s /q "%%i"
del /s /q *.pyc

echo Rebuilding the executable...
pyinstaller main.spec --noconfirm

pause
