# Deployment Guide

## Server Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Virtual environment support
- Nginx (for production web server)
- Supervisor or systemd (for process management)

## Step-by-Step Deployment

### 1. Server Access and Initial Setup

```bash
# SSH into your college server
ssh your_username@your_server_ip

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3-pip python3-venv nginx git -y
```

### 2. Clone Your Repository on Server

```bash
# Navigate to web directory (or your preferred location)
cd /var/www/  # or /home/your_username/

# Clone your repository
git clone https://github.com/Garora22/A-Web-Service-for-Students-Evaluation.git
cd A-Web-Service-for-Students-Evaluation

# Or if you already cloned, just pull latest changes
git pull origin main
```

### 3. Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production server (gunicorn)
pip install gunicorn
```

### 4. Configure Environment Variables

```bash
# Create .env file on server
nano .env
```

Add your environment variables (DO NOT commit .env to git):
```
SECRET_KEY=your-new-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your_server_ip,your_domain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=Your Name <your_email@gmail.com>
```

### 5. Prepare Django Application

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

### 6. Test with Gunicorn

```bash
# Test if gunicorn works
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Visit http://your_server_ip:8000 to test
# Press Ctrl+C to stop
```

### 7. Configure Gunicorn as a Service

Create systemd service file:
```bash
sudo nano /etc/systemd/system/django-app.service
```

Add this configuration:
```ini
[Unit]
Description=Django Application
After=network.target

[Service]
User=your_username
Group=www-data
WorkingDirectory=/var/www/A-Web-Service-for-Students-Evaluation
Environment="PATH=/var/www/A-Web-Service-for-Students-Evaluation/venv/bin"
ExecStart=/var/www/A-Web-Service-for-Students-Evaluation/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/A-Web-Service-for-Students-Evaluation/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl start django-app
sudo systemctl enable django-app
sudo systemctl status django-app
```

### 8. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/django-app
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your_server_ip your_domain.com;

    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/A-Web-Service-for-Students-Evaluation/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/A-Web-Service-for-Students-Evaluation/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/A-Web-Service-for-Students-Evaluation/gunicorn.sock;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/django-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Accessing Your Website

- **URL**: `http://your_server_ip` or `http://your_domain.com`
- **Admin Panel**: `http://your_server_ip/admin`

## Updating Your Code

### From Your Local Machine:

```bash
# Make changes to your code
# Commit and push to GitHub
git add .
git commit -m "Your update message"
git push origin main
```

### On the Server:

```bash
# SSH into server
ssh your_username@your_server_ip

# Navigate to project directory
cd /var/www/A-Web-Service-for-Students-Evaluation

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run migrations (if any)
python manage.py migrate

# Collect static files (if changed)
python manage.py collectstatic --noinput

# Restart the application
sudo systemctl restart django-app
```

## Quick Update Script

Create an update script for easier deployments:

```bash
nano ~/update_django.sh
```

Add:
```bash
#!/bin/bash
cd /var/www/A-Web-Service-for-Students-Evaluation
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart django-app
echo "Deployment completed!"
```

Make it executable:
```bash
chmod +x ~/update_django.sh
```

Run updates with:
```bash
~/update_django.sh
```

## Troubleshooting

### Check Application Status
```bash
sudo systemctl status django-app
```

### View Logs
```bash
# Django app logs
sudo journalctl -u django-app -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
sudo systemctl restart django-app
sudo systemctl restart nginx
```

## Security Checklist

- [ ] Changed SECRET_KEY in production
- [ ] Set DEBUG=False
- [ ] Configured ALLOWED_HOSTS
- [ ] .env file is not in git repository
- [ ] Set up SSL/HTTPS (use Let's Encrypt)
- [ ] Regular backups of database
- [ ] Keep dependencies updated
