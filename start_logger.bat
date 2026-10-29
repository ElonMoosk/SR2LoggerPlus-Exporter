@echo off
chcp 65001 >nul
cd /d "%~dp0"
python sr2_logger.py
echo.
echo Receiver stopped.
pause
