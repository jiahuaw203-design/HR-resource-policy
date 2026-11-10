@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   人力资源政策雷达 - 一键更新
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [失败] 没有找到 Python。
  echo 请先到 python.org 下载安装，安装时记得勾选 "Add Python to PATH"。
  echo.
  pause
  exit /b 1
)

echo [1/2] 检查依赖...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
  echo [提示] 依赖安装可能没成功，继续尝试抓取。
)

echo.
echo [2/2] 开始抓取，大约需要 1-2 分钟，请勿关闭窗口...
python fetch_policies.py
if errorlevel 1 (
  echo.
  echo [失败] 抓取出错，请把上面的报错信息复制下来排查。
  pause
  exit /b 1
)

echo.
echo 完成。接下来打开 index.html 看一眼，再上传到 GitHub 即可。
pause
