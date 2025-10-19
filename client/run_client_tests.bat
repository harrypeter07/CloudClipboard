@echo off
echo ====================================
echo   CloudClipboard Client Test Suite
echo ====================================
echo.

echo [INFO] Testing client connection to deployed server...
echo [INFO] Server URL: https://cloudclipboard.onrender.com
echo.

echo [INFO] Starting client tests...
echo.

python test_client.py

echo.
echo ====================================
echo   Client Test Suite Complete
echo ====================================
echo.
pause
