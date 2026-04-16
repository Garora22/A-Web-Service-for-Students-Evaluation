# Quick Start Guide for Server Deployment

## 🎯 Quick Summary

This guide will help you deploy your Django website to your college server in 3 main phases:
1. **Push code to server**
2. **Set up and run the application**
3. **Access and update the website**

---

## 📤 Phase 1: Push Code to Server

### Option A: Using Git (Recommended)

On your **college server**:

```bash
# SSH into your server
ssh your_username@your_server_ip

# Navigate to web directory
cd /var/www/  # or /home/your_username/

# Clone your repository
git clone https://github.com/Garora22/A-Web-Service-for-Students-Evaluation.git
cd A-Web-Service-for-Students-Evaluation
```

### Option B: Using SCP (File Transfer)

From your **local machine**:

```bash
# Transfer entire project folder
scp -r /Users/snehasissatapathy/Desktop/UGP/A-Web-Service-for-Students-Evaluation \
    your_username@your_server_ip:/var/www/
```

---

## 🛠️ Phase 2: Set Up on Server

On your **college server**:

```bash
# Run the automated setup script
cd /var/www/A-Web-Service-for-Students-Evaluation
bash setup_server.sh

# Edit environment variables
nano .env
# Update: SECRET_KEY, DEBUG=False, ALLOWED_HOSTS=your_server_ip

# Create admin user
source venv/bin/activate
python manage.py createsuperuser
```

### Manual Setup (if script fails)

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Setup database
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

---

## 🚀 Phase 3: Run the Application

### Quick Test (Development Server)

```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Visit: `http://your_server_ip:8000`

**Note:** This is only for testing! For production, continue below.

### Production Setup (with Gunicorn + Nginx)

Follow the detailed steps in `DEPLOYMENT.md` to:
1. Configure Gunicorn as a service
2. Set up Nginx as reverse proxy
3. Enable automatic restart

---

## 🌐 Accessing Your Website

Once deployed:

- **Main Website**: `http://your_server_ip`
- **Admin Panel**: `http://your_server_ip/admin`
- **Login Page**: `http://your_server_ip/accounts/login/`

---

## 🔄 Updating Your Website

### From Your Local Computer:

```bash
# Make changes to code
# Then commit and push
git add .
git commit -m "Updated feature X"
git push origin main
```

### On Your Server:

```bash
# SSH to server
ssh your_username@your_server_ip

# Navigate to project
cd /var/www/A-Web-Service-for-Students-Evaluation

# Run deployment script
bash deploy.sh
```

**OR manually:**

```bash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart django-app  # If using systemd service
```

---

## ⚠️ Important Security Notes

Before deploying to production:

1. **Generate a new SECRET_KEY**
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```
   Add this to your `.env` file

2. **Set DEBUG=False** in `.env`

3. **Set ALLOWED_HOSTS** to your server IP/domain in `.env`

4. **Never commit .env** to git (already in .gitignore)

---

## 🐛 Troubleshooting

### Check if app is running:
```bash
sudo systemctl status django-app
```

### View error logs:
```bash
sudo journalctl -u django-app -f
```

### Restart services:
```bash
sudo systemctl restart django-app
sudo systemctl restart nginx
```

### Check what's using port 8000:
```bash
sudo lsof -i :8000
```

---

## 📚 Need More Details?

- **Full deployment steps**: See `DEPLOYMENT.md`
- **Project setup**: See `README.md`
- **Issues**: Check logs or contact system admin

---

## 🎓 Common College Server Scenarios

### If you don't have sudo access:

You can still run the app without Nginx:
```bash
# Use gunicorn directly
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Ask your IT department to:
- Open port 8000 in firewall
- Or set up Nginx proxy for you

### If port 8000 is blocked:

Try different ports:
```bash
python manage.py runserver 0.0.0.0:8080
# or
gunicorn config.wsgi:application --bind 0.0.0.0:8080
```

### If server reboots frequently:

Set up systemd service (see DEPLOYMENT.md) so app auto-starts.

---

**Good luck with your deployment! 🚀**
