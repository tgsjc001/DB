@echo off
REM Set the working directory to the script's location
cd /d %~dp0

REM Optional: activate virtual environment if you use one
REM call venv\Scripts\activate

REM Run the New Show Wizard
python ChangeDBscript.py

pause