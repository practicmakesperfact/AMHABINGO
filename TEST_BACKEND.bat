@echo off
echo Testing backend connection...
echo.

curl http://localhost:8000/health

echo.
echo.
echo If you see {"status":"healthy"} above, backend is working!
echo If you see an error, backend is not running.
echo.
pause
