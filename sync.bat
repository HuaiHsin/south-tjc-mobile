@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
python sync.py
echo.
echo ============================================
echo  完成。按任意鍵關閉視窗。
echo ============================================
pause >nul
