@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
python sync.py
if errorlevel 1 (
  echo.
  echo [提醒] 找不到 python 指令，請改用 py sync.py，或確認 Python 已加入 PATH。
)
echo.
echo ============================================
echo  完成。按任意鍵關閉視窗。
echo ============================================
pause >nul
