@echo off
setlocal
pushd "%~dp0"
python -m pip install -r requirements.txt
python src/ultimate_automation_system.py
popd
echo.
echo 종료하려면 아무 키나 누르세요...
pause>nul

