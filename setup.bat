@echo off
setlocal

REM Triptych setup script (Windows)
REM Checks prerequisites, installs deps, starts the server, opens the browser.

echo.
echo === Triptych setup ===
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js not found. Install from https://nodejs.org/ ^(version 18 or newer^).
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo Python not found. Install from https://www.python.org/ ^(version 3.10 or newer^).
    pause
    exit /b 1
  )
)

if not exist "node_modules" (
  echo Installing Node dependencies...
  call npm install
  if errorlevel 1 (
    echo npm install failed.
    pause
    exit /b 1
  )
) else (
  echo Node dependencies already installed.
)

if exist "requirements.txt" (
  echo Installing Python dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo pip install failed - continuing anyway, some displays may not work.
  )
)

if not exist ".env" (
  if exist ".env.example" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example. Edit it if you are on API billing.
  )
)

echo.
echo Starting Triptych at http://localhost:3000
echo Press Ctrl+C to stop.
echo.

REM Open the browser after a short delay (server takes a moment to bind)
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:3000"

call npm run dev

endlocal
