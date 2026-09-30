@echo off
REM 打包 HKAB_CNHHKD.py 成 EXE（無 console，單一檔案）
pyinstaller --noconsole --onefile --icon=..\icon.ico HKAB_CNHHKD.py
pause 