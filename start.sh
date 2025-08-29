#!/usr/bin/env bash
set -euo pipefail

echo "Starting startup script..."

# Optional: wait for Redis to be available (quick pause)
sleep 2

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A MOTA worker --loglevel=info --concurrency=1 &
CELERY_PID=$!

# Handle shutdown signals to stop Celery properly
function _term() {
  echo "Shutting down Celery (PID $CELERY_PID)..."
  kill -TERM "$CELERY_PID" 2>/dev/null || true
  wait "$CELERY_PID" || true
  exit 0
}
trap _term SIGTERM

# Start Django using Gunicorn in the foreground (so Render considers it "up")
echo "Starting Gunicorn web server..."
exec gunicorn MOTA.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2
