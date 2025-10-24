@echo off
echo ====================================
echo   CloudClipboard - Build Script
echo ====================================
echo.

cd ..\client

echo [1/4] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/4] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo [3/4] Building EXE with proper configuration...
pyinstaller --clean CloudClipboard.spec

if errorlevel 1 (
    echo.
    echo ❌ BUILD FAILED!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [4/4] Final cleanup...
rmdir /s /q build

echo.
echo ====================================
echo   ✅ BUILD COMPLETE!
echo ====================================
echo.
echo Your EXE is located at:
echo   client\dist\CloudClipboard.exe
echo.
echo To test:
echo 1. Start the server: cd ..\server && python main.py
echo 2. Run the EXE: dist\CloudClipboard.exe
echo.
pause
