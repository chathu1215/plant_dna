@echo off
title Plant DNA Identification System - Ruhuna BST
cd /d "%~dp0desktop_app"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error. Press any key to close...
    pause >nul
)
