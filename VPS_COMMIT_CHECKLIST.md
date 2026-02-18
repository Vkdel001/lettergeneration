# VPS Commit Checklist - SMS Links & Email Features

## 📁 Files to Commit to GitHub

### ✅ **Core SMS Link Files (MUST COMMIT)**
```
generate_sms_links.py                    # SMS link generation script
src/components/FolderBasedSMSSection.jsx # SMS links frontend component
```

### ✅ **Core Email Notification Files (MUST COMMIT)**
```
completion_email_service.py             # Email notification service
src/components/EmailConfigSection.jsx   # Email config frontend component
```

### ✅ **Modified Core Files (MUST COMMIT)**
```
server.js                               # Updated with SMS & email endpoints
src/App.jsx                            # Added new components and tabs
src/components/TabNavigation.jsx        # Added SMS Links and Email tabs
pdf_generator_wrapper.py               # Added email notifications
```

### ✅ **Testing & Documentation Files (RECOMMENDED)**
```
test_email_system.py                   # Email testing script
check_email_status.py                  # Email status checker
VPS_UPDATE_GUIDE_SMS_EMAIL.md         # Update guide
VPS_COMMIT_CHECKLIST.md               # This file
```

### ❌ **Files NOT to Commit**
```
.env                                   # Contains sensitive API keys
letter_links/                          # Generated SMS link data
output_*/                             # Generated PDF folders
temp_uploads/                         # Temporary upload files
*.xlsx                                # Excel files with customer data
```

---

## 🔧 Required Code Changes for VPS

### 1. **Update `completion_email_service.py`** (CRITICAL)

**Current Issue**: Hardcoded localhost URL in email templates

**Find this line** (around line 85):
```python
<a href="http://localhost:3001" style="...">
```

**Replace with**:
```python
<a href="https://your-actual-domain.com" style="...">
```

**Also find** (around line 185):
```python
<a href="http://localhost:3001" style="...">
```

**Replace with**:
```python
<a href="https://your-actual-domain.com" style="...">
```

### 2. **Update `src/App.jsx`** (OPTIONAL - Already Dynamic)

**Current code** (around line 15):
```javascript
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:3001'
  : `${window.location.protocol}//${window.location.hostname}`;
```

**This is already correct** - it automatically detects production domain. No changes needed.

### 3. **Update `.gitignore`** (CRITICAL)

**Add these lines** to your `.gitignore` file:
```gitignore
# Environment files
.env
.env.local
.env.production

# Generated content
letter_links/
output_*/
temp_uploads/

# Customer data
*.xlsx
Generic_Template*.xlsx

# Logs
*.log
logs/

# Python cache
__pycache__/
*.pyc
```

---

## 🚀 Deployment Commands

### 1. **Before Committing** (Local)
```bash
# Check what files will be committed
git status

# Add only the required files
git add generate_sms_links.py
git add completion_email_service.py
git add src/components/FolderBasedSMSSection.jsx
git add src/components/EmailConfigSection.jsx
git add server.js
git add src/App.jsx
git add src/components/TabNavigation.jsx
git add pdf_generator_wrapper.py
git add test_email_system.py
git add check_email_status.py
git add .gitignore

# Commit changes
git commit -m "Add SMS Links and Email Notifications features

- Add SMS link generation with folder-based approach
- Add email notifications for PDF and SMS completion
- Add new frontend tabs for SMS links and email config
- Update server with new API endpoints
- Add testing scripts for email functionality"

# Push to GitHub
git push origin main
```

### 2. **On VPS Server**
```bash
# SSH into your VPS
ssh your-user@your-vps-ip

# Navigate to project directory
cd /var/www/your-project-directory

# Pull latest changes
git pull origin main

# Install new Python dependencies
pip install sib-api-v3-sdk python-dotenv

# Rebuild frontend
npm run build

# Restart application
pm2 restart your-app-name
```

---

## 🔧 VPS Configuration Changes

### 1. **Update `.env` file on VPS**

**Add these variables** to your existing `.env` file on the VPS:
```bash
# SSH into VPS and edit .env
sudo nano /var/www/your-project/.env

# Add these lines:
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=system@your-domain.com
SENDER_NAME=NIC Mauritius System
REPLY_TO_EMAIL=support@your-domain.com
REPLY_TO_NAME=NIC Support
USER_EMAIL=admin@your-domain.com
USER_NAME=NICL Admin
```

### 2. **Create Required Directories**
```bash
# Create letter_links directory
mkdir -p /var/www/your-project/letter_links

# Set permissions
sudo chown -R www-data:www-data /var/www/your-project/letter_links
sudo chmod -R 755 /var/www/your-project/letter_links
```

### 3. **Update Domain in Email Templates** (On VPS)

**Edit the file on VPS**:
```bash
sudo nano /var/www/your-project/completion_email_service.py
```

**Find and replace** (use Ctrl+W to search):
- Search for: `http://localhost:3001`
- Replace with: `https://your-actual-domain.com`

**There are 2 instances to replace** (around lines 85 and 185)

---

## ✅ Testing Checklist (After Deployment)

### 1. **Test Email System**
```bash
# On VPS, test email configuration
python check_email_status.py

# Send test email
python test_email_system.py your-email@example.com
```

### 2. **Test SMS Links**
1. Go to your website: `https://your-domain.com`
2. Login to the system
3. Look for **"SMS Links"** tab
4. Select a folder with existing PDFs
5. Click **"Generate SMS"**
6. Test the generated links

### 3. **Test Email Notifications**
1. Go to **"Email Notifications"** tab
2. Configure your email address
3. Generate some PDFs (should get email notification)
4. Generate SMS links (should get email notification)

---

## 🚨 Critical Points

### **MUST DO Before Committing:**
1. ✅ Update `.gitignore` to exclude sensitive files
2. ✅ Replace `localhost:3001` with your domain in `completion_email_service.py`
3. ✅ Ensure no `.env` file is committed
4. ✅ Ensure no customer data (`.xlsx` files) is committed

### **MUST DO On VPS:**
1. ✅ Add `BREVO_API_KEY` to `.env` file
2. ✅ Install Python packages: `sib-api-v3-sdk python-dotenv`
3. ✅ Create `letter_links` directory with proper permissions
4. ✅ Restart application after deployment

### **Domain-Specific Changes:**
Replace `your-actual-domain.com` with your real domain in:
- `completion_email_service.py` (2 locations)
- VPS `.env` file (SENDER_EMAIL, REPLY_TO_EMAIL)

---

## 📋 Quick Command Summary

### **Local (Before Commit):**
```bash
# Update completion_email_service.py with your domain
# Update .gitignore
# Commit and push files
git add [files listed above]
git commit -m "Add SMS Links and Email Notifications"
git push origin main
```

### **VPS (After Commit):**
```bash
git pull origin main
pip install sib-api-v3-sdk python-dotenv
mkdir -p letter_links && chmod 755 letter_links
# Edit .env file to add BREVO_API_KEY
npm run build
pm2 restart your-app-name
```

### **Test:**
```bash
python check_email_status.py
python test_email_system.py your-email@example.com
# Test website functionality
```

---

**Total Files to Commit**: 8 core files + 4 optional files  
**Critical Code Changes**: 1 file (`completion_email_service.py`)  
**VPS Configuration**: Add environment variables + create directory  
**Estimated Time**: 15-20 minutes total