@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title SR2 Logger Plus - 一键安装
rem 安装到游戏用户数据目录，AI 助手/工具都能直接找到
set "GAMEDATA=%USERPROFILE%\AppData\LocalLow\Jundroo\SimpleRockets 2\UserData"
set "TARGET=%GAMEDATA%\SR2LoggerPlus"
set "SRC=%~dp0"

echo ==========================================
echo   SR2 飞行日志导出工具 - 一键安装
echo ==========================================
echo.

rem ---- 1. 检查 Python ----
echo [1/4] 检查 Python...
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo   [!] 没找到 Python，正在尝试用 winget 安装...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo   [x] 没有 winget，请手动安装 Python 3.8+：
        echo       https://www.python.org/downloads/
        echo       安装时勾选 "Add Python to PATH"
        pause
        exit /b 1
    )
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    echo.
    echo   [i] Python 已安装，请关闭本窗口重新运行安装器。
    pause
    exit /b 0
)
for /f "delims=" %%v in ('python --version 2^>^&1') do echo       %%v OK

rem ---- 2. 创建目录 ----
echo [2/4] 创建安装目录...
if not exist "%GAMEDATA%" (
    echo   [!] 没找到游戏数据目录：
    echo       %GAMEDATA%
    echo       请先运行一次游戏，或手动修改本文件里的 GAMEDATA 路径。
    echo       仍然继续安装到当前盘符的用户目录...
    set "TARGET=%USERPROFILE%\SR2LoggerPlus"
)
if not exist "%TARGET%" mkdir "%TARGET%"
echo       %TARGET%

rem ---- 3. 复制文件 ----
echo [3/4] 复制文件...
if not exist "%SRC%sr2_logger.py" (
    echo   [x] 找不到 sr2_logger.py，请确认安装器和它在同一文件夹。
    pause
    exit /b 1
)
copy /y "%SRC%sr2_logger.py" "%TARGET%\" >nul
> "%TARGET%\start_logger.bat" (
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%%~dp0"
    echo python sr2_logger.py
    echo echo.
    echo echo Receiver stopped.
    echo pause
)
> "%TARGET%\README-给AI看.txt" (
    echo 这个目录存放 SR2 飞行日志导出工具的输出。
    echo.
    echo 文件说明:
    echo   flight.jsonl   结构化遥测，每行一个 JSON，字段见 field=... 键
    echo   messages.txt   游戏内 Vizzy 广播的原始文本，每行一条
    echo.
    echo 字段速查:
    echo   kind=state  15字段: 时间,高度,高度ASL,平速,垂速,X,Y,Z,VX,VY,VZ,纬度,经度,距靶,地形高度
    echo   kind=guid   13字段: 时间,纵差,横差,预测距,俯仰,倾侧,推力,燃料,气密,阻力,俯仰角,滚转目标,攻角
    echo   标签行: WAIT / LAND / GD / ZLT / FD
    echo.
    echo 启动: 双击 start_logger.bat，出现 "监听 udp://127.0.0.1:2837" 即为就绪
    echo 模组: https://www.simplerockets.com/Mods/View/64864/SR2LoggerPlus
)
echo       OK

rem ---- 4. 桌面快捷方式 ----
echo [4/4] 创建桌面快捷方式...
powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\启动日志接收端.lnk'); $s.TargetPath='%TARGET%\start_logger.bat'; $s.WorkingDirectory='%TARGET%'; $s.Save()" 2>nul
if errorlevel 1 (echo       跳过) else (echo       OK)

echo.
echo ==========================================
echo   安装完成！
echo ==========================================
echo.
echo   安装位置（游戏数据目录内，AI 可直接读取）:
echo     %TARGET%
echo.
echo   下一步：
echo     1. 装模组 https://www.simplerockets.com/Mods/View/64864/SR2LoggerPlus
echo     2. 双击桌面「启动日志接收端」
echo     3. 进游戏飞一次，数据自动写入上面的目录
echo.
pause
