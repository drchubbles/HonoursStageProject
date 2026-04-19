@echo off
rem Set your environment variables such as SECRET_KEY, DB_USER, DB_PASS, and any Microsoft Graph values before running this on a real deployment.
cd /d "%~dp0"

if not exist "env\Scripts\python.exe" (
  py -3 -m venv env
)

call "env\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python app.py
pause
