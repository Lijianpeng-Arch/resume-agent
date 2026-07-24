@echo off
chcp 65001 >nul

REM 检测 Python 是否安装
where python >nul 2>nul
if errorlevel 1 (
    echo ============================================================
    echo   启动失败：未检测到 Python
    echo ============================================================
    echo.
    echo   这个项目需要 Python 3.7 或更高版本。
    echo.
    echo   下载地址：https://www.python.org/downloads/
    echo.
    echo   安装时请务必勾选：
    echo     [x] Add Python to PATH
    echo.
    echo   安装完成后，重新双击 start.cmd 即可。
    echo ============================================================
    echo.
    pause
    exit /b 1
)

REM 检测 Python 版本
python -c "import sys; sys.exit(0 if sys.version_info >= (3,7) else 1)"
if errorlevel 1 (
    echo ============================================================
    echo   启动失败：Python 版本过低
    echo ============================================================
    echo.
    echo   当前版本：
    python --version
    echo.
    echo   需要 Python 3.7 或更高版本。
    echo   下载地址：https://www.python.org/downloads/
    echo ============================================================
    echo.
    pause
    exit /b 1
)

python "%~dp0start.py"
if errorlevel 1 pause