@echo off
echo ====================================
echo   CloudClipboard API Test Suite
echo ====================================
echo.

echo [INFO] Make sure the server is running on http://localhost:8000
echo [INFO] If not, start it with: python main.py
echo.

echo [INFO] Starting API tests...
echo.

python test_api.py

echo.
echo ====================================
echo   Test Suite Complete
echo ====================================
echo.
pause
