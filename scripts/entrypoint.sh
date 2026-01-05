#!/bin/bash
set -e

cat << 'EOF'

 .----------------.  .----------------.  .----------------.  .----------------.
| .--------------. || .--------------. || .--------------. || .--------------. |
| |  ____  ____  | || |     ____     | || |  _________   | || |      __      | |
| | |_   ||   _| | || |   .'    `.   | || | |  _   _  |  | || |     /  \     | |
| |   | |\/| |   | || |  /  .--.  \  | || | |_/ | | \_|  | || |    / /\ \    | |
| |   | |  | |   | || |  | |    | |  | || |     | |      | || |   / ____ \   | |
| |  _| |_ | |_  | || |  \  `--'  /  | || |    _| |_     | || | _/ /    \ \_ | |
| | |____||____| | || |   `.____.'   | || |   |_____|    | || ||____|  |____|| |
| |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------'

EOF

echo "📡 Waiting for the database to be ready..."
sleep 5

# ✅ RUN MIGRATIONS ONLY IF ENABLED
if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "🛠️ Running migrations..."
  python manage.py migrate --noinput

  echo "📦 Collecting static files..."
  python manage.py collectstatic --noinput --clear

  echo "🌐 Compiling translations..."
  python manage.py compilemessages -i .venv -i node_modules -l fr
else
  echo "⏭️ Skipping migrations (worker container)"
fi

echo "🚀 Starting: $@"
exec "$@"
