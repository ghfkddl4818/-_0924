@echo off
setlocal
pushd "%~dp0"
python -m pip install -r requirements.txt
python src/ultimate_automation_system.py
popd
echo.
echo �����Ϸ��� �ƹ� Ű�� ��������...
pause>nul

