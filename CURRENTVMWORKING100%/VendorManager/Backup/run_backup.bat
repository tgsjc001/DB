@echo off
:: Get current script directory
cd /d %~dp0

:: Run backup.py using default Python interpreter
python backup.py

:: Optional log
echo [%date% %time%] Backup executed >> backup_log.txt
