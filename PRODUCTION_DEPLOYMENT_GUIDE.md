# NICL Letter System - Production Deployment Guide

## 📋 Overview

This document outlines the necessary steps and considerations for deploying the NICL Letter System to production, including the new SMS Link and Email Notification features.

## 🔒 Security & Configuration (CRITICAL - Phase 1)

### Environment Variables Setup

#### 1. Create Production Environment File
Create `.env.production` with the following variables:

```env
# Production URLs
PRODUCTION_BASE_URL=https://your-domain.com
FRONTEND_URL=https://your-domain.com
API_BASE_URL=https://your-domain.com

# Email Configuration
BREVO_API_KEY=your_production_brevo_key
SENDER_EMAIL=system@your-domain.com
SENDER_NAME=NIC Mauritius System
REPLY_TO_EMAIL=support@your-domain.com
REPLY_TO_NAME=NIC Support

# ZwennPay Configuration
ZWENNPAY_MERCHANT_ID=151

# File Paths (Production)
UPLOAD_PATH=/var/www/nicl/uploads
PDF_OUTPUT_PATH=/var/www/nicl/pdfs
LETTER_LINKS_PATH=/var/www/nicl/letter_links

# Security
NODE_ENV=production
SESSION_SECRET=your_secure_session_secret_here

# Database (if applicable)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nicl_letters
DB_USER=nicl_user
DB_PASS=secure_password_here
```

#### 2. Update .gitignore
Ensure the following files are excluded from Git:

```gitignore
# Environment files
.env
.env.local
.env.production
.env.staging

# Sensitive files
*.xlsx
*.pdf
temp_uploads/
output_*/
letter_links/
generated_pdfs/

# Logs
*.log
logs/

# Node modules
node_modules/

# Python cache
__pycache__/
*.pyc

# Build files
dist/
build/
```

### Files Requiring URL Configuration Updates

#### High Priority Files:
1. **`src/App.jsx`** - Frontend API base URL detection
2. **`completion_email_service.py`** - Email template URLs
3. **`generate_sms_links.py`** - SMS link base URL
4. **`server.js`** - Letter viewer URLs
5. **All PDF templates** - QR code generation endpoints

#### Required Changes:
- Replace hardcoded `localhost:3001` with environment variables
- Update email templates to use production domain
- Configure SMS link base URLs dynamically
- Update QR code API endpoints

## 🌐 Production Environment Setup (Phase 2)

### VPS Server Requirements

#### System Requirements:
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **RAM**: Minimum 4GB (8GB recommended for large files)
- **Storage**: 50GB+ SSD (for PDF storage)
- **CPU**: 2+ cores
- **Network**: Stable internet for API calls

#### Required Software:
```bash
# Node.js (v18+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.9+
sudo apt-get install python3 python3-pip python3-venv

# System dependencies
sudo apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    imagemagick \
    fonts-liberation \
    fonts-dejavu-core \
    build-essential

# PM2 for process management
sudo npm install -g pm2
```

### Python Environment Setup

#### 1. Create Virtual Environment:
```bash
cd /var/www/nicl-letters
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Python Dependencies:
Create `requirements.txt`:
```txt
pandas==2.0.3
openpyxl==3.1.2
reportlab==4.0.4
Pillow==10.0.0
requests==2.31.0
segno==1.5.2
qrcode==7.4.2
sib-api-v3-sdk==7.6.0
python-dotenv==1.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Node.js Environment Setup

#### 1. Install Dependencies:
```bash
npm install --production
```

#### 2. Build Frontend:
```bash
npm run build
```

## 🔧 Configuration Files (Phase 2)

### Nginx Configuration
Create `/etc/nginx/sites-available/nicl-letters`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # File upload limits
    client_max_body_size 100M;
    
    # Serve static files
    location / {
        root /var/www/nicl-letters/dist;
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
        proxy_read_timeout 300s;
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
}
```

### PM2 Configuration
Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'nicl-letters',
    script: 'server.js',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '2G',
    env: {
      NODE_ENV: 'production',
      PORT: 3001
    },
    error_file: '/var/log/nicl-letters/error.log',
    out_file: '/var/log/nicl-letters/out.log',
    log_file: '/var/log/nicl-letters/combined.log',
    time: true
  }]
};
```

## 📁 File Structure & Permissions

### Directory Structure:
```
/var/www/nicl-letters/
├── server.js
├── package.json
├── ecosystem.config.js
├── .env.production
├── dist/                    # Built frontend
├── uploads/                 # Temporary uploads
├── output_*/               # Generated PDFs
├── letter_links/           # SMS link data
├── fonts/                  # Font files
├── logs/                   # Application logs
├── venv/                   # Python virtual environment
└── scripts/                # Python scripts
```

### Set Permissions:
```bash
# Create directories
sudo mkdir -p /var/www/nicl-letters/{uploads,logs}
sudo mkdir -p /var/log/nicl-letters

# Set ownership
sudo chown -R www-data:www-data /var/www/nicl-letters
sudo chown -R www-data:www-data /var/log/nicl-letters

# Set permissions
sudo chmod -R 755 /var/www/nicl-letters
sudo chmod -R 777 /var/www/nicl-letters/uploads
sudo chmod -R 777 /var/www/nicl-letters/output_*
sudo chmod -R 777 /var/www/nicl-letters/letter_links
```

## 🚀 Deployment Process (Phase 3)

### Pre-Deployment Checklist

#### Code Preparation:
- [ ] Update all hardcoded URLs to use environment variables
- [ ] Remove sensitive data from code
- [ ] Update `.gitignore` file
- [ ] Create `.env.example` file
- [ ] Test email system with production SMTP
- [ ] Test SMS links with production domain
- [ ] Verify all Python dependencies
- [ ] Build and test frontend

#### Server Preparation:
- [ ] VPS server provisioned
- [ ] Domain name configured
- [ ] SSL certificate installed
- [ ] Required software installed
- [ ] Firewall configured
- [ ] Backup strategy implemented

### Deployment Steps:

#### 1. Clone Repository:
```bash
cd /var/www
sudo git clone https://github.com/your-username/nicl-letters.git
cd nicl-letters
```

#### 2. Setup Environment:
```bash
# Copy production environment file
sudo cp .env.example .env.production
sudo nano .env.production  # Edit with production values

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Node.js
npm install --production
npm run build
```

#### 3. Configure Services:
```bash
# Setup Nginx
sudo ln -s /etc/nginx/sites-available/nicl-letters /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL
sudo certbot --nginx -d your-domain.com

# Start application
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🔍 Testing & Monitoring

### Production Testing:

#### 1. Functionality Tests:
- [ ] PDF generation with various templates
- [ ] SMS link generation and access
- [ ] Email notifications
- [ ] File upload and download
- [ ] User authentication
- [ ] QR code generation

#### 2. Performance Tests:
- [ ] Large file processing (1000+ records)
- [ ] Concurrent user access
- [ ] Memory usage monitoring
- [ ] Disk space monitoring

#### 3. Security Tests:
- [ ] HTTPS enforcement
- [ ] File upload restrictions
- [ ] API endpoint security
- [ ] Environment variable protection

### Monitoring Setup:

#### 1. Application Monitoring:
```bash
# PM2 monitoring
pm2 monit

# Log monitoring
tail -f /var/log/nicl-letters/combined.log
```

#### 2. System Monitoring:
```bash
# Disk usage
df -h

# Memory usage
free -h

# Process monitoring
htop
```

## 🛠️ Maintenance & Updates

### Regular Maintenance:

#### Daily:
- Monitor application logs
- Check disk space usage
- Verify email delivery

#### Weekly:
- Clean up old temporary files
- Review error logs
- Update system packages

#### Monthly:
- Backup generated PDFs
- Review security logs
- Update dependencies

### Update Process:

#### 1. Backup Current Version:
```bash
sudo cp -r /var/www/nicl-letters /var/www/nicl-letters-backup-$(date +%Y%m%d)
```

#### 2. Deploy Updates:
```bash
cd /var/www/nicl-letters
sudo git pull origin main
npm install --production
npm run build
pm2 restart nicl-letters
```

## 🚨 Troubleshooting

### Common Issues:

#### 1. Email Not Sending:
- Check BREVO_API_KEY in environment
- Verify email configuration in web interface
- Check application logs for email errors
- Test with `python test_email_system.py`

#### 2. SMS Links Not Working:
- Verify production domain in SMS links
- Check letter_links directory permissions
- Verify QR code generation
- Test individual letter URLs

#### 3. PDF Generation Failing:
- Check Python virtual environment
- Verify font files are present
- Check output directory permissions
- Monitor memory usage during generation

#### 4. File Upload Issues:
- Check Nginx client_max_body_size
- Verify upload directory permissions
- Check disk space availability

### Emergency Contacts:
- System Administrator: [contact info]
- Brevo Support: https://help.brevo.com
- Domain/SSL Provider: [contact info]

## 📞 Support Information

### Log Locations:
- Application logs: `/var/log/nicl-letters/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

### Useful Commands:
```bash
# Restart application
pm2 restart nicl-letters

# Check application status
pm2 status

# View logs
pm2 logs nicl-letters

# Check Nginx status
sudo systemctl status nginx

# Reload Nginx configuration
sudo systemctl reload nginx

# Check SSL certificate
sudo certbot certificates
```

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Next Review**: January 2025

**Note**: This document should be updated whenever new features are added or configuration changes are made.