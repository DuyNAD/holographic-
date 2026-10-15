@echo off
rem Double-click to set up Holographic Studio (runs setup.ps1 without changing the
rem machine's PowerShell execution policy). Extra arguments are passed through,
rem e.g.  setup.cmd -Run
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 (
    echo.
    echo Cai dat that bai - xem thong bao loi o tren.
    pause
    exit /b 1
)
