@echo off
chcp 65001 >nul
python "%~dp0start.py"
if errorlevel 1 pause
