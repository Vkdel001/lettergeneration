# NICL Letter Generation System - Project Handover Documentation
## Part 2: Installation & Deployment

---

## 🚀 Fresh Installation Guide

### Prerequisites

#### VPS Server Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **RAM**: Minimum 4GB (8GB recommended for 5000+ records)
- **Storage**: 50GB+ SSD
- **CPU**: 2+ cores
- **Network**: Stable internet for API calls

#### Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.9+
sudo apt-get install -y python3 python3-pip python3-venv

# Install Nginx
sudo apt-get install -y nginx

# Install Certbot for SSL
sudo apt-get install -y certbot python3-certbot-nginx

# Install PM2 globally
sudo npm install -g pm2

# Install system dependencies for PDF generation
sudo apt-get install -y imagemagick fonts-liberation fonts-dejavu-core build-essential
```

---

## 📦 Installation Steps

### Step 1: Clone Repository
```bash
# Create project directory
sudo mkdir -p /var/www
cd /var/www

# Clone from GitHub
sudo git clone https://github.com/Vkdel001/lettergeneration.git pdf-generator
cd pdf-generator

# Set ownership
sudo chown -R $USER:$USER /var/www/pdf-generator
```

### Step 2: Setup Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install pandas==2.0.3 openpyxl==3.1.2 reportlab==4.0.4 Pillow==10.0.0 \
            requests==2.31.0 segno==1.5.2 qrcode==7.4.2 PyPDF2==3.0.1 \
            PyMuPDF==1.23.8 sib-api-v3-sdk==7.6.0 python-dotenv==1.0.0

# Verify critical packages
python -c "import pandas, reportlab, fitz; print('All packages installed')"

# Deactivate for now
deactivate
```

### Step 3: Setup Node.js Environment
```bash
# Install Node dependencies
npm install

# Build frontend for production
npm run build

# Verify build
ls -la dist/
```

### Step 4: Configure Environment Variables
```bash
# Create .env file
cat > .env << 'EOF'
# Email Configuration (Brevo)
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=system@niclmauritius.site
SENDER_NAME=NIC Mauritius System
REPLY_TO_EMAIL=support@niclmauritius.site
REPLY_TO_NAME=NIC Support

# User Email for Notifications
USER_EMAIL=admin@niclmauritius.site
USER_NAME=NICL Admin

# ZwennPay Configuration
ZWENNPAY_MERCHANT_ID=151

# Node Environment
NODE_ENV=production
PORT=3001
EOF

# Secure the .env file
chmod 600 .env
```

### Step 5: Create Required Directories
```bash
# Create output directories
mkdir -p temp_uploads letter_links

# Set permissions
chmod 755 temp_uploads letter_links
```

### Step 6: Configure PM2
```bash
# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'pdf-generator',
    script: 'server.js',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '2G',
    env: {
      NODE_ENV: 'production',
      PORT: 3001
    },
    error_file: '/var/log/pdf-generator/error.log',
    out_file: '/var/log/pdf-generator/out.log',
    log_file: '/var/log/pdf-generator/combined.log',
    time: true
  }]
};
EOF

# Create log directory
sudo mkdir -p /var/log/pdf-generator
sudo chown -R $USER:$USER /var/log/pdf-generator

# Start application
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Follow the command it outputs
```

---

## 🌐 Domain & SSL Configuration

### Step 1: Configure DNS
At your domain registrar (Namecheap, etc.):

**For arrears.niclmauritius.site**:
```
Type: A Record
Host: arrears
Value: YOUR_VPS_IP_ADDRESS
TTL: Automatic
```

**For nicl.ink**:
```
Type: A Record
Host: @
Value: YOUR_VPS_IP_ADDRESS
TTL: Automatic

Type: A Record
Host: www
Value: YOUR_VPS_IP_ADDRESS
TTL: Automatic
```

### Step 2: Configure Nginx for Main Domain
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/arrears.niclmauritius.site
```

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name arrears.niclmauritius.site;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name arrears.niclmauritius.site;
    
    # SSL Configuration (will be added by certbot)
    
    # File upload limits
    client_max_body_size 50M;
    
    # Serve static files
    location / {
        root /var/www/pdf-generator/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API routes
    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 7200s;
        proxy_connect_timeout 75s;
    }
    
    # Letter viewer routes
    location /letter/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Logs
    access_log /var/log/nginx/arrears.access.log;
    error_log /var/log/nginx/arrears.error.log;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/arrears.niclmauritius.site /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 3: Configure Nginx for Short URL Domain
```bash
# Create Nginx configuration for nicl.ink
sudo nano /etc/nginx/sites-available/nicl.ink
```

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name nicl.ink www.nicl.ink;
    return 301 https://nicl.ink$request_uri;
}

# HTTPS server for short URLs
server {
    listen 443 ssl http2;
    server_name nicl.ink www.nicl.ink;
    
    # SSL Configuration (will be added by certbot)
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy all requests to Node.js
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Health check
    location /health {
        return 200 "nicl.ink OK";
        add_header Content-Type text/plain;
    }
    
    # Logs
    access_log /var/log/nginx/nicl.ink.access.log;
    error_log /var/log/nginx/nicl.ink.error.log;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/nicl.ink /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 4: Install SSL Certificates
```bash
# Install SSL for main domain
sudo certbot --nginx -d arrears.niclmauritius.site

# Install SSL for short URL domain
sudo certbot --nginx -d nicl.ink -d www.nicl.ink

# Verify certificates
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## ✅ Verification Checklist

### Test Installation
```bash
# 1. Check PM2 status
pm2 status
# Should show: pdf-generator | online

# 2. Check server logs
pm2 logs pdf-generator --lines 20
# Should show: "PDF Generation Server running at http://localhost:3001"

# 3. Test Python environment
source venv/bin/activate
python -c "import pandas, reportlab, fitz; print('Python OK')"
deactivate

# 4. Test API endpoint
curl -I http://localhost:3001/api/status
# Should return: HTTP/1.1 200 OK

# 5. Test main domain
curl -I https://arrears.niclmauritius.site
# Should return: HTTP/2 200

# 6. Test short URL domain
curl -I https://nicl.ink/health
# Should return: HTTP/2 200

# 7. Test Nginx configuration
sudo nginx -t
# Should return: syntax is ok

# 8. Check SSL certificates
sudo certbot certificates
# Should show both domains with valid certificates
```

### Test PDF Generation
1. Go to https://arrears.niclmauritius.site
2. Upload sample Excel file
3. Select template (e.g., SPH_Fresh.py)
4. Click "Generate PDFs"
5. Verify PDFs are created in output folder
6. Check QR codes are visible in individual PDFs

### Test SMS Link Generation
1. Generate PDFs first (above)
2. Go to "SMS Links" tab
3. Select the output folder
4. Click "Generate SMS"
5. Download SMS CSV file
6. Test one short URL from CSV
7. Verify letter viewer loads on mobile

---

## 🔧 Post-Installation Configuration

### Configure Firewall
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Setup Automatic Backups
```bash
# Create backup script
sudo nano /usr/local/bin/backup-pdf-generator.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/pdf-generator"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup code (excluding node_modules and venv)
tar -czf $BACKUP_DIR/code_$DATE.tar.gz \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='output_*' \
    --exclude='temp_uploads' \
    /var/www/pdf-generator

# Backup environment file
cp /var/www/pdf-generator/.env $BACKUP_DIR/env_$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "env_*" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-pdf-generator.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add line:
0 2 * * * /usr/local/bin/backup-pdf-generator.sh
```

---

**Continue to Part 3: Operations & Maintenance**