#!/bin/bash

# Deployment script for 0123.ru file hosting
# Run this script on your VPS as root or with sudo

set -e  # Exit on any error

echo "🚀 Starting deployment of 0123.ru file hosting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="filehost"
PROJECT_DIR="/var/www/$PROJECT_NAME"
SERVICE_USER="www-data"
SERVICE_GROUP="www-data"
PYTHON_VERSION="3.11"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root or with sudo${NC}"
   exit 1
fi

echo -e "${YELLOW}📋 Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}📦 Installing required packages...${NC}"
apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib redis-server nginx \
    libpq-dev build-essential libmagic1 \
    supervisor ufw fail2ban

echo -e "${YELLOW}🔧 Configuring PostgreSQL...${NC}"
# Create database and user
sudo -u postgres createuser --interactive --pwprompt $SERVICE_USER
sudo -u postgres createdb $PROJECT_NAME

echo -e "${YELLOW}🔒 Configuring Redis...${NC}"
# Redis is already installed and running

echo -e "${YELLOW}📁 Creating project directory...${NC}"
mkdir -p $PROJECT_DIR
chown $SERVICE_USER:$SERVICE_GROUP $PROJECT_DIR

echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
cd $PROJECT_DIR
python3 -m venv venv
chown -R $SERVICE_USER:$SERVICE_GROUP venv

echo -e "${YELLOW}📥 Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt

echo -e "${YELLOW}⚙️ Configuring Django...${NC}"
# Copy environment file
cp env.production .env
chown $SERVICE_USER:$SERVICE_GROUP .env
chmod 600 .env

# Generate secret key
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
sed -i "s/your-super-secret-key-here-change-this/$SECRET_KEY/" .env

# Update server IP in .env
SERVER_IP=$(curl -s ifconfig.me)
sed -i "s/YOUR_SERVER_IP/$SERVER_IP/g" .env

echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
python manage.py migrate --settings=filehost.settings_prod

echo -e "${YELLOW}📁 Collecting static files...${NC}"
python manage.py collectstatic --noinput --settings=filehost.settings_prod

echo -e "${YELLOW}🔧 Setting up Gunicorn...${NC}"
mkdir -p /var/log/gunicorn
chown $SERVICE_USER:$SERVICE_GROUP /var/log/gunicorn

# Copy Gunicorn config
cp gunicorn.conf.py $PROJECT_DIR/
chown $SERVICE_USER:$SERVICE_GROUP $PROJECT_DIR/gunicorn.conf.py

echo -e "${YELLOW}⚙️ Setting up systemd service...${NC}"
# Copy service file
cp filehost.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable filehost

echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
# Copy Nginx config
cp nginx.conf /etc/nginx/sites-available/$PROJECT_NAME
sed -i "s/YOUR_SERVER_IP/$SERVER_IP/g" /etc/nginx/sites-available/$PROJECT_NAME

# Enable site
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t

echo -e "${YELLOW}🔒 Configuring firewall...${NC}"
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl start filehost
systemctl restart nginx

echo -e "${YELLOW}✅ Checking service status...${NC}"
systemctl status filehost --no-pager
systemctl status nginx --no-pager

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "1. Update your domain DNS to point to: $SERVER_IP"
echo -e "2. When domain is ready, update .env file:"
echo -e "   - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,$SERVER_IP"
echo -e "   - SITE_BASE_URL=https://yourdomain.com"
echo -e "   - USE_HTTPS=True"
echo -e "3. Configure SSL certificate (Let's Encrypt recommended)"
echo -e "4. Restart services: systemctl restart filehost nginx"
echo -e ""
echo -e "${GREEN}🌐 Your file hosting is now available at: http://$SERVER_IP${NC}"
echo -e "${GREEN}📊 Monitor logs: journalctl -u filehost -f${NC}"
