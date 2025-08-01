@echo off
setlocal

:: ==== CONFIGURE THESE ====
set PGUSER=TGSAdmin
set PGPASSWORD=Donttazemebro5212
set PGHOST=10.0.0.6
set PGPORT=5212
set PGDATABASE=TGSDB_apr_2025
set BACKUPDIR=C:\TGSBackup

:: ==== TIMESTAMPED FILE ====
set BACKUPFILE=%BACKUPDIR%\%PGDATABASE%_backup_%DATE:~10,4%-%DATE:~4,2%-%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%.backup

:: ==== CREATE BACKUP DIR IF NEEDED ====
if not exist "%BACKUPDIR%" (
    mkdir "%BACKUPDIR%"
)

:: ==== RUN BACKUP ====
echo Backing up database %PGDATABASE% to %BACKUPFILE%
"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -F c -f "%BACKUPFILE%" -h %PGHOST% -p %PGPORT% -U %PGUSER% %PGDATABASE%

echo Backup complete.
endlocal
pause
