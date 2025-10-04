@echo off
chcp 65001 >nul
title 屏幕录制工具环境检测与启动

echo ========================================
echo   屏幕录制工具环境检测与启动
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python环境检测通过
echo.

:: 运行环境检测和修复
echo 正在检查依赖环境...
python check_environment.py

if errorlevel 1 (
    echo.
    echo ❌ 环境检测失败，请手动检查依赖
    pause
    exit /b 1
)

echo.
echo ✅ 环境准备完成，启动录屏工具...
python Super_Hi_Vision.py

pause