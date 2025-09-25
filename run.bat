@echo off
chcp 65001 >nul
title 录屏工具启动器

echo.
echo ================================
echo   录屏工具环境检查与启动
echo ================================
echo.

:: 检查Python
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未在PATH中
    pause
    exit /b 1
)

:: 检查必要包
echo 检查Python依赖包...
set "error_found=0"

for %%p in (PIL pynput psutil requests numpy) do (
    python -c "import %%p" >nul 2>&1
    if errorlevel 1 (
        echo 错误: %%p 未安装
        set "error_found=1"
    ) else (
        echo 成功: %%p 已安装
    )
)

if %error_found% equ 1 (
    echo.
    echo 尝试自动安装缺失的包...
    for %%p in (PIL pynput psutil requests numpy) do (
        python -c "import %%p" >nul 2>&1
        if errorlevel 1 (
            echo 正在安装 %%p...
            pip install %%p -i https://pypi.tuna.tsinghua.edu.cn/simple/ --trusted-host pypi.tuna.tsinghua.edu.cn --quiet
            if errorlevel 1 (
                echo 安装 %%p 失败
            ) else (
                echo 安装 %%p 成功
            )
        )
    )
)

:: 检查脚本是否存在
if not exist "Super_Hi_Vision.py" (
    echo 错误: 未找到Super_Hi_Vision.py
    pause
    exit /b 1
)

echo.
echo 环境检查完成，启动录屏工具...
echo.

:: 启动录屏工具
python Super_Hi_Vision.py

echo.
echo 录屏工具已退出
pause