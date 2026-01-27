@echo off
cd /d "%~dp0"

if not exist "env\Scripts\python.exe" (
  py -3 -m venv env
)

call "env\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python app.py
pause
