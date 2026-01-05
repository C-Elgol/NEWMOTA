#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

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

echo "🛠️ Running migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# echo "🌐 Compiling translations..."
python manage.py compilemessages -i .venv -i node_modules -l fr # French

# echo "✅ Translation Compilation Complete"

# 🚀 Execute the container command (gunicorn, celery, etc.)
echo "🚀 Starting: $@"
exec "$@"
