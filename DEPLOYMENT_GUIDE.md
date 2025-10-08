# PDF Generator VPS Deployment Guide
Complete step-by-step guide to deploy your PDF Generator app on DigitalOcean VPS with all critical fixes and improvements applied.

## 🚨 Critical Updates (October 2025)
This guide includes essential fixes for:
- **QR Code Corruption Prevention** - PyMuPDF integration
- **Python Compatibility** - Fixed `python` vs `python3` issues  
- **Environment-Aware API URLs** - Automatic local/VPS detection
- **Password Protection** - PyPDF2 version compatibility
- **JavaScript Error Fixes** - Resolved frontend issues

## 📋 Pre-Deployment Checklist

### Current Setup:
- ✅ Existing Streamlit app in `/var/www/cashback`
- ✅ PDF Generator app ready on GitHub
- ✅ VPS with available resources

## 🚀 Step-by-Step Deployment

### Step 1: Connect to Your VPS
```bash
# SSH into your DigitalOcean VPS
ssh root@your-vps-ip
# or
ssh your-username@your-vps-ip
```

### Step 2: Check Current System Status
```bash
# Check available resources
echo "=== System Resources ==="
free -h
df -h
htop  # Press 'q' to quit

# Check running processes
echo "=== Running Services ==="
ps aux | grep streamlit
ps aux | grep python
netstat -tlnp | grep :8501  # Check if Streamlit is running
```

### Step 3: Install Required Dependencies

#### Install Node.js (if not already installed)
```bash
# Check if Node.js is installed
node --version
npm --version

# If not installed, install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

#### Install Python Dependencies
```bash
# Check Python version
python3 --version

# Install pip if not available
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-full

# 🔧 CRITICAL FIX: Create python symlink for compatibility
sudo ln -sf /usr/bin/python3 /usr/bin/python
python --version  # Should show Python 3.x

# Install required Python packages (with system override for newer Ubuntu)
pip3 install pandas openpyxl reportlab segno requests python-dotenv PyPDF2 --break-system-packages

# 🚨 CRITICAL: Install PyMuPDF for QR code preservation
pip3 install PyMuPDF --break-system-packages

# Verify critical packages
python3 -c "import fitz; print('✅ PyMuPDF installed - QR codes will be preserved')"
python3 -c "from PyPDF2 import PdfReader; print('✅ PyPDF2 compatible')"
```

### Step 4: Create Directory Structure
```bash
# Navigate to web directory
cd /var/www

# Create directory for PDF Generator
sudo mkdir -p pdf-generator
sudo chown $USER:$USER pdf-generator
cd pdf-generator
```

### Step 5: Clone and Setup Application
```bash
# Clone your repository
git clone https://github.com/Vkdel001/lettergeneration.git .

# Install Node.js dependencies
npm install

# Create environment file
cp .env.example .env 2>/dev/null || touch .env

# Edit environment file with your API keys
nano .env
```

#### Add to .env file:
```env
# Brevo API Configuration
BREVO_API_KEY=your-actual-brevo-api-key-here

# Email Configuration
DEFAULT_SENDER_EMAIL=noreply@nic.mu
DEFAULT_SENDER_NAME=NIC Insurance

# ZwennPay Configuration (if needed)
ZWENNPAY_MERCHANT_ID=151
```

### Step 6: Setup Fonts Directory
```bash
# Create fonts directory
mkdir -p fonts

# Upload your Cambria font files to the fonts directory
# You'll need to transfer cambria.ttf and cambriab.ttf
# Option 1: Use SCP from your local machine
# scp cambria.ttf cambriab.ttf root@your-vps-ip:/var/www/pdf-generator/fonts/

# Option 2: Download if you have them hosted somewhere
# wget -O fonts/cambria.ttf "your-font-url"
# wget -O fonts/cambriab.ttf "your-bold-font-url"

# Set proper permissions
chmod 644 fonts/*.ttf
```

### Step 7: Build the Application
```bash
# 🔧 IMPORTANT: The frontend now has environment-aware API URLs
# It automatically detects if running locally or on VPS
# Local: uses http://localhost:3001
# VPS: uses http://your-vps-ip:3001

# Build the frontend with environment detection
npm run build

# Test if the server starts
npm run server &
sleep 5
curl http://localhost:3001/api/status
kill %1  # Stop the test server

# 🧪 Test Python scripts work correctly
python3 JPH_Fresh.py --help
python3 combine_pdfs.py --help
```

### Step 8: Install Process Manager (PM2)
```bash
# Install PM2 globally
sudo npm install -g pm2

# Check if PM2 is already managing your Streamlit app
pm2 list
```

### Step 9: Configure PM2 for Both Apps

#### Create PM2 ecosystem file
```bash
# Create PM2 configuration
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'streamlit-cashback',
      cwd: '/var/www/cashback',
      script: 'streamlit',
      args: 'run app.py --port 8501 --server.address 0.0.0.0',
      interpreter: 'python3',
      env: {
        PYTHONPATH: '/var/www/cashback'
      },
      restart_delay: 1000,
      max_restarts: 5
    },
    {
      name: 'pdf-generator',
      cwd: '/var/www/pdf-generator',
      script: 'server.js',
      interpreter: 'node',
      env: {
        NODE_ENV: 'production',
        PORT: 3001
      },
      restart_delay: 1000,
      max_restarts: 5
    }
  ]
};
EOF
```

### Step 10: Start Applications with PM2
```bash
# Stop any existing PM2 processes (if any)
pm2 stop all
pm2 delete all

# Start both applications
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Follow the instructions provided by the command above
```

### Step 11: Configure Firewall
```bash
# Check current firewall status
sudo ufw status

# Allow necessary ports
sudo ufw allow 8501  # Streamlit app
sudo ufw allow 3001  # PDF Generator
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (if using SSL)

# Enable firewall if not already enabled
sudo ufw --force enable

# Check status
sudo ufw status
```

### Step 12: Test Both Applications
```bash
# Test Streamlit app
curl -I http://localhost:8501

# Test PDF Generator
curl -I http://localhost:3001/api/status

# Check from external access (replace with your VPS IP)
curl -I http://your-vps-ip:8501
curl -I http://your-vps-ip:3001/api/status
```

### Step 13: Setup Nginx Reverse Proxy (Optional but Recommended)
```bash
# Install Nginx if not already installed
sudo apt-get install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/apps << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP

    # Streamlit Cashback App
    location /cashback/ {
        proxy_pass http://localhost:8501/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # PDF Generator App
    location /pdf-generator/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Default redirect
    location / {
        return 301 /cashback/;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/apps /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🔧 Maintenance Commands

### Check Application Status
```bash
# PM2 status
pm2 status
pm2 logs pdf-generator
pm2 logs streamlit-cashback

# System resources
htop
df -h
free -h
```

### Restart Applications
```bash
# Restart specific app
pm2 restart pdf-generator
pm2 restart streamlit-cashback

# Restart all apps
pm2 restart all
```

### Update PDF Generator App
```bash
cd /var/www/pdf-generator
git pull origin main
npm install
npm run build
pm2 restart pdf-generator
```

## 🌐 Access URLs

After deployment, your apps will be accessible at:

### Direct Access (Port-based):
- **Streamlit App:** `http://your-vps-ip:8501`
- **PDF Generator:** `http://your-vps-ip:3001`

### With Nginx (Path-based):
- **Streamlit App:** `http://your-domain.com/cashback/`
- **PDF Generator:** `http://your-domain.com/pdf-generator/`

## 🚨 Troubleshooting

### Critical Issues and Fixes:

#### 1. 🔴 Connection Refused Errors
```bash
# Check if services are running
pm2 status

# Check API URL configuration (frontend should auto-detect)
curl -I http://localhost:3001/api/status

# Restart services
pm2 restart all

# Check logs for errors
pm2 logs pdf-generator --lines 20
```

#### 2. 🔴 Python Script Failures
```bash
# Verify Python symlink (CRITICAL FIX)
python --version  # Should show Python 3.x
which python      # Should point to /usr/bin/python

# If symlink is broken, recreate it
sudo rm /usr/bin/python 2>/dev/null
sudo ln -sf /usr/bin/python3 /usr/bin/python

# Test Python scripts
python3 JPH_Fresh.py --help
python3 combine_pdfs.py --help
```

#### 3. 🔴 QR Code Corruption in Combined PDFs
```bash
# Check if PyMuPDF is installed (CRITICAL for QR preservation)
python3 -c "import fitz; print('PyMuPDF available')" || echo "❌ PyMuPDF missing!"

# Install PyMuPDF if missing
pip3 install PyMuPDF --break-system-packages

# Test PDF combining with QR preservation
python3 combine_pdfs.py --files '["file1.pdf", "file2.pdf"]' --output test.pdf
```

#### 4. 🔴 Password Protection Not Working
```bash
# Check PyPDF2 compatibility
python3 -c "from PyPDF2 import PdfReader, PdfWriter; print('PyPDF2 v3+ compatible')" || \
python3 -c "from PyPDF2 import PdfFileReader; print('PyPDF2 v2 compatible')"

# Test password protection
python3 JPH_Fresh.py --output test_password_output
# Check if protected folder has password-protected PDFs
```

#### 5. 🔴 Frontend JavaScript Errors
```bash
# Check browser console for errors like:
# - "text.normalize is not a function"
# - "emailData is not defined"

# These are fixed in the latest code - ensure you have the latest build
git pull
npm run build
pm2 restart pdf-frontend
```

#### 6. 🔴 Environment Detection Issues
```bash
# The frontend should automatically detect environment
# Check browser network tab - API calls should go to correct URL:
# Local: http://localhost:3001/api/*
# VPS: http://your-vps-ip:3001/api/*

# If wrong URLs, clear browser cache and hard refresh (Ctrl+F5)
```

### Standard Issues:

#### Port Already in Use:
```bash
# Find process using port
sudo netstat -tlnp | grep :3001
sudo kill -9 <process-id>
```

#### Permission Issues:
```bash
# Fix ownership
sudo chown -R $USER:$USER /var/www/pdf-generator
chmod +x /var/www/pdf-generator/server.js
```

#### Font Issues:
```bash
# Check fonts exist
ls -la /var/www/pdf-generator/fonts/
# Ensure cambria.ttf and cambriab.ttf are present
```

#### Memory Issues:
```bash
# Check memory usage
free -h
# If low on memory, consider adding swap
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 🔍 Diagnostic Commands:
```bash
# Complete system check
echo "=== Python Environment ==="
python --version
python3 --version
which python

echo "=== Critical Packages ==="
python3 -c "import fitz; print('✅ PyMuPDF')" 2>/dev/null || echo "❌ PyMuPDF missing"
python3 -c "from PyPDF2 import PdfReader; print('✅ PyPDF2')" 2>/dev/null || echo "❌ PyPDF2 missing"

echo "=== Services Status ==="
pm2 status

echo "=== Network Status ==="
sudo netstat -tlnp | grep -E ':(3001|8080|8501)'

echo "=== API Health ==="
curl -I http://localhost:3001/api/status 2>/dev/null || echo "❌ API not responding"
```

## 📊 Monitoring Setup

### Create monitoring script:
```bash
cat > /var/www/monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status $(date) ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h /
echo ""
echo "PM2 Status:"
pm2 status
echo ""
echo "Port Status:"
netstat -tlnp | grep -E ':(8501|3001)'
EOF

chmod +x /var/www/monitor.sh

# Add to crontab for regular monitoring
(crontab -l 2>/dev/null; echo "0 */6 * * * /var/www/monitor.sh >> /var/log/app-monitor.log") | crontab -
```

## ✅ Deployment Checklist

### Basic Setup:
- [ ] SSH access to VPS
- [ ] System resources checked
- [ ] Node.js installed
- [ ] Python dependencies installed
- [ ] Repository cloned
- [ ] Environment variables configured
- [ ] Font files uploaded

### Critical Fixes Applied:
- [ ] **Python symlink created** (`python` → `python3`)
- [ ] **PyMuPDF installed** (QR code preservation)
- [ ] **PyPDF2 compatibility verified** (password protection)
- [ ] **Environment-aware frontend built** (auto API detection)
- [ ] **JavaScript errors fixed** (normalize, emailData issues)

### Deployment Complete:
- [ ] Application built successfully
- [ ] PM2 configured and running
- [ ] Firewall configured
- [ ] Both apps accessible
- [ ] Nginx configured (optional)
- [ ] Monitoring setup

### Final Verification:
- [ ] **PDF generation works** (test with sample Excel file)
- [ ] **QR codes preserved** in combined PDFs
- [ ] **Password protection works** (check protected folder)
- [ ] **Email integration works** (Brevo emails sent)
- [ ] **No JavaScript errors** in browser console

## 🎉 Success!

Once all steps are completed, you'll have both applications running on your VPS:
- Your existing Streamlit cashback app
- Your new PDF Generator app with all critical fixes

Both will be managed by PM2 and automatically restart if they crash or if the server reboots.

## 🔧 Critical Fixes Summary

### What We Fixed:
1. **QR Code Corruption** - Switched to PyMuPDF for better image preservation
2. **Python Compatibility** - Fixed `python` vs `python3` command issues
3. **Environment Detection** - Frontend automatically detects local vs VPS
4. **Password Protection** - Added PyPDF2 version compatibility
5. **JavaScript Errors** - Fixed `normalize` and `emailData` scope issues
6. **Error Handling** - Added robust error checking and logging

### Why These Fixes Matter:
- **Prevents customer letter disasters** (QR codes missing)
- **Ensures cross-environment compatibility** (local dev + VPS production)
- **Improves reliability** (better error handling)
- **Maintains security** (password protection works)

### Version Information:
- **Last Updated:** October 2025
- **Critical Fixes Applied:** QR preservation, Python compatibility, environment detection
- **Dependencies:** PyMuPDF (recommended), PyPDF2 (fallback), PM2, Node.js 18+

---

**⚠️ IMPORTANT:** Always test PDF generation and combining after deployment to ensure QR codes are preserved correctly. This prevents critical issues that could affect customer communications.