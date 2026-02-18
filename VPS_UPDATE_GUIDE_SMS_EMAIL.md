# VPS Update Guide - SMS Links & Email Notifications

## 📋 Overview

This guide covers updating your **existing live VPS deployment** to add the new SMS Link and Email Notification features.

**Estimated Update Time**: 15-30 minutes  
**Downtime Required**: 2-3 minutes (for server restart)

---

## 🔧 Pre-Update Preparation

### 1. Backup Current System
```bash
# SSH into your VPS
ssh your-user@your-vps-ip

# Create backup
sudo cp -r /var/www/your-project /var/www/your-project-backup-$(date +%Y%m%d)

# Backup database if applicable
# mysqldump or pg_dump commands here
```

### 2. Check Current System Status
```bash
# Check if server is running
pm2 status

# Check current Git status
cd /var/www/your-project
git status
git log --oneline -5
```

---

## 📧 Email Notification Setup

### 1. Update Environment Variables

Add these to your existing `.env` file:
```bash
# Edit your production .env file
sudo nano /var/www/your-project/.env

# Add these new variables:
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=system@your-domain.com
SENDER_NAME=NIC Mauritius System
REPLY_TO_EMAIL=support@your-domain.com
REPLY_TO_NAME=NIC Support
USER_EMAIL=admin@your-domain.com
USER_NAME=NICL Admin
```

### 2. Install Email Dependencies
```bash
# Activate Python virtual environment (if you have one)
source venv/bin/activate

# Install new Python packages
pip install sib-api-v3-sdk python-dotenv

# Or update requirements.txt and install
pip install -r requirements.txt
```

### 3. Test Email Configuration
```bash
# Test email system
python check_email_status.py

# Send test email (replace with your email)
python test_email_system.py your-email@example.com
```

---

## 📱 SMS Links Setup

### 1. Create Required Directories
```bash
# Create letter_links directory if it doesn't exist
mkdir -p /var/www/your-project/letter_links

# Set proper permissions
sudo chown -R www-data:www-data /var/www/your-project/letter_links
sudo chmod -R 755 /var/www/your-project/letter_links
```

### 2. Update Domain Configuration

**Important**: Replace `localhost:3001` with your actual domain in these files:

#### A. Update `completion_email_service.py`:
```bash
sudo nano completion_email_service.py

# Find and replace:
# FROM: http://localhost:3001
# TO: https://your-actual-domain.com
```

#### B. Update `generate_sms_links.py`:
```bash
sudo nano generate_sms_links.py

# The base URL will be passed from server, but verify it's using your domain
```

#### C. Update `server.js` (if needed):
```bash
sudo nano server.js

# Verify API_BASE detection works with your domain
# Should automatically detect production domain
```

---

## 🚀 Deploy New Features

### 1. Pull Latest Code
```bash
cd /var/www/your-project

# Stash any local changes
git stash

# Pull latest changes
git pull origin main

# If you have conflicts, resolve them
git stash pop  # if you had local changes
```

### 2. Install New Dependencies

#### Node.js Dependencies:
```bash
# Install any new npm packages
npm install

# Rebuild frontend
npm run build
```

#### Python Dependencies:
```bash
# Install new Python packages
pip install sib-api-v3-sdk python-dotenv

# Or if you have requirements.txt
pip install -r requirements.txt
```

### 3. Update File Permissions
```bash
# Ensure new files have correct permissions
sudo chown -R www-data:www-data /var/www/your-project
sudo chmod +x *.py  # Make Python scripts executable
```

---

## 🔄 Restart Services

### 1. Restart Application
```bash
# Restart your Node.js application
pm2 restart your-app-name

# Or restart all PM2 processes
pm2 restart all

# Check status
pm2 status
pm2 logs your-app-name --lines 20
```

### 2. Reload Nginx (if needed)
```bash
# Test Nginx configuration
sudo nginx -t

# Reload if configuration is OK
sudo systemctl reload nginx
```

---

## ✅ Verify New Features

### 1. Test Email Notifications

#### A. Configure Email in Web Interface:
1. Go to your website: `https://your-domain.com`
2. Login to the system
3. Click on **"Email Notifications"** tab
4. Enter your email address and name
5. Click **"Save Configuration"**
6. Should see: ✅ "Email configuration saved successfully!"

#### B. Test Email System:
```bash
# Run email test from server
python test_email_system.py your-email@example.com

# Check logs for email sending
pm2 logs your-app-name | grep EMAIL
```

### 2. Test SMS Links

#### A. Generate SMS Links:
1. Go to **"SMS Links"** tab in web interface
2. Select a folder with existing PDFs
3. Click **"Generate SMS"**
4. Should see processing and completion
5. Click **"Download SMS"** to get CSV file

#### B. Test SMS Link Access:
1. Open the downloaded CSV file
2. Copy one of the ShortURL links
3. Open in browser (preferably mobile)
4. Should see the letter with QR code
5. Test PDF download from letter viewer

### 3. Test Integration
1. Generate new PDFs (should get email notification)
2. Generate SMS links (should get email notification)
3. Verify both features work together

---

## 🔍 Troubleshooting

### Common Issues & Solutions:

#### 1. Email Not Sending
```bash
# Check email configuration
python check_email_status.py

# Check application logs
pm2 logs your-app-name | grep EMAIL

# Verify .env file has BREVO_API_KEY
cat .env | grep BREVO
```

#### 2. SMS Links Not Working
```bash
# Check letter_links directory
ls -la letter_links/

# Check permissions
ls -la letter_links/*/

# Test individual letter URL
curl -I https://your-domain.com/letter/some-letter-id
```

#### 3. New Tab Not Showing
```bash
# Clear browser cache
# Hard refresh (Ctrl+F5)

# Check if frontend was rebuilt
ls -la dist/

# Restart application
pm2 restart your-app-name
```

#### 4. Python Dependencies Missing
```bash
# Install missing packages
pip install sib-api-v3-sdk python-dotenv

# Check Python path
which python
python --version

# Activate virtual environment if needed
source venv/bin/activate
```

---

## 📊 Verification Checklist

After update, verify these work:

- [ ] **Email Configuration**: Can set email in web interface
- [ ] **PDF Generation**: Still works + sends email notification
- [ ] **SMS Link Generation**: New tab appears and works
- [ ] **SMS Link Access**: Links work on mobile devices
- [ ] **QR Codes**: Display in letter viewer
- [ ] **PDF Download**: Works from letter viewer
- [ ] **Existing Features**: All previous functionality still works

---

## 🔄 Rollback Plan (If Needed)

If something goes wrong:

```bash
# Stop current application
pm2 stop your-app-name

# Restore backup
sudo rm -rf /var/www/your-project
sudo mv /var/www/your-project-backup-$(date +%Y%m%d) /var/www/your-project

# Restart application
pm2 start your-app-name

# Check status
pm2 status
```

---

## 📞 Post-Update Support

### Log Locations:
- Application logs: `pm2 logs your-app-name`
- Nginx logs: `/var/log/nginx/error.log`
- Email test logs: Run `python check_email_status.py`

### Useful Commands:
```bash
# Check application status
pm2 status

# View recent logs
pm2 logs your-app-name --lines 50

# Restart if needed
pm2 restart your-app-name

# Test email system
python test_email_system.py your-email@example.com

# Check SMS link generation
ls -la letter_links/
```

---

## 🎯 Summary

This update adds:
- ✅ **Email Notifications** for PDF and SMS completion
- ✅ **SMS Links** tab for generating customer notification links
- ✅ **QR Codes** in mobile-friendly letter viewer
- ✅ **Email Configuration** interface

**Total new files added**: ~8 files  
**Modified existing files**: ~6 files  
**New dependencies**: 2 Python packages  

The update is designed to be **non-breaking** - all existing functionality continues to work while adding the new features.

---

**Update Guide Version**: 1.0  
**Compatible with**: Existing NICL Letter System deployments  
**Last Updated**: December 2024