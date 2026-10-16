@echo off
title Building Standalone Windows Executable (.exe)
cd /d "%~dp0"
echo ========================================================
echo Building Plant DNA Identification System Standalone EXE
echo ========================================================
echo.
echo [1/3] Checking / Installing PyInstaller...
pip install pyinstaller
echo.
echo [2/3] Compiling standalone executable with PyQt6...
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "Cleaned_Plant_DNA_Barcoding_Data.csv;." ^
    --add-data "images;images" ^
    --name "Plant_DNA_Identification_System" ^
    main.py
echo.
echo [3/3] Build completed!
echo Executable is located in: %~dp0dist\Plant_DNA_Identification_System\Plant_DNA_Identification_System.exe
echo.
pause
