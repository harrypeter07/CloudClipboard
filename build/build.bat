@echo off
echo ====================================
echo   Cloud Clipboard - Build Script
echo ====================================
echo.

cd ..\client

echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [2/3] Building EXE...
pyinstaller --onefile --windowed --noconsole --name=CloudClipboard --hidden-import=pystray --hidden-import=PIL._tkinter_finder --hidden-import=win32timezone clipboard_manager.py

echo.
echo [3/3] Cleaning up...
rmdir /s /q build
del CloudClipboard.spec

echo.
echo ====================================
echo   BUILD COMPLETE!
echo ====================================
echo.
echo Your EXE is located at:
echo   client\dist\CloudClipboard.exe
echo.
pause
