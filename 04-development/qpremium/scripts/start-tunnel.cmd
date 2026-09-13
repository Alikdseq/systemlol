@echo off
REM Deprecated: tunnel now runs inside Docker.
REM Use:  docker compose up -d
REM Or only tunnel:  docker compose up -d tunnel
cd /d "%~dp0\.."
docker compose up -d tunnel
echo.
echo Tunnel service started in Docker. Check: docker compose logs -f tunnel
pause
