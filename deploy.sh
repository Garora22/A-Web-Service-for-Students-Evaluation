 #!/bin/bash

# Deployment script for Django application (simple runserver mode)
# Usage: ./deploy.sh

set -e

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code from git..."
git pull origin main

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Stop old runserver process if running
echo "🛑 Stopping previous runserver process (if any)..."
pkill -f "manage.py runserver 0.0.0.0:8000" || true

# Start runserver in background
echo "▶️  Starting runserver in background..."
nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &

echo "✅ Deployment completed successfully!"
echo "🌐 App should be available at: http://<server-ip>:8000"
echo "📄 Logs: tail -f server.log"
