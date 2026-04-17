#!/bin/bash

# Initial server setup script (simple runserver mode)
# Run this ONCE on your server after cloning the repository
# Usage: bash setup_server.sh

set -e

echo "🏗️  Setting up Django app (simple mode)..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️  Warning: This script is designed for Linux servers"
fi

# Update system and install Python tools
echo "📦 Installing required packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env file with your actual values!"
    echo "   Run: nano .env"
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create static files directory
# Create media directory
mkdir -p media

echo ""
echo "✅ Basic setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your actual configuration"
echo "   nano .env"
echo ""
echo "2. Create a superuser for Django admin"
echo "   source venv/bin/activate"
echo "   python manage.py createsuperuser"
echo ""
echo "3. Start server:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "4. To keep it running after logout:"
echo "   nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &"
echo ""
echo "📖 Full instructions are in DEPLOYMENT.md"
