#!/usr/bin/env bash
# Triptych setup script (macOS/Linux)
# Checks prerequisites, installs deps, starts the server, opens the browser.

set -e

cd "$(dirname "$0")"

echo
echo "=== Triptych setup ==="
echo

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found. Install from https://nodejs.org/ (version 18 or newer)."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "Python not found. Install from https://www.python.org/ (version 3.10 or newer)."
  exit 1
fi

PYTHON_CMD="python3"
command -v python3 >/dev/null 2>&1 || PYTHON_CMD="python"

if [ ! -d "node_modules" ]; then
  echo "Installing Node dependencies..."
  npm install
else
  echo "Node dependencies already installed."
fi

if [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies..."
  $PYTHON_CMD -m pip install -r requirements.txt || \
    echo "pip install failed - continuing anyway, some displays may not work."
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp ".env.example" ".env"
  echo "Created .env from .env.example. Edit it if you are on API billing."
fi

echo
echo "Starting Triptych at http://localhost:3000"
echo "Press Ctrl+C to stop."
echo

# Open the browser after a short delay (server takes a moment to bind)
(
  sleep 3
  if command -v open >/dev/null 2>&1; then
    open http://localhost:3000
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:3000
  fi
) &

exec npm run dev
