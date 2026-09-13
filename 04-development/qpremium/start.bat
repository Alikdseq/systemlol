@echo off
cd /d "%~dp0"
echo Starting Q Premium via Docker Compose...
docker compose up --build -d
echo.
echo API:  http://localhost:8000/api/v1/health/
echo Admin Django: http://localhost:8000/admin/
echo Logs: docker compose logs -f backend
pause
