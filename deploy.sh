#!/bin/bash

# Deployment script for Django application
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

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Restart application service
echo "♻️  Restarting application..."
sudo systemctl restart django-app

echo "✅ Deployment completed successfully!"
echo "🌐 Your website should now be updated."
