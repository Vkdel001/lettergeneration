# VPS Python Dependencies Fix - Missing pandas Module

## 🚨 **Real Issue Identified**

The 500 error is NOT a route conflict - it's because **Python dependencies are missing** on your VPS server. The error shows:

```
ModuleNotFoundError: No module named 'pandas'
```

## 🔧 **Quick Fix Commands for VPS**

Run these commands on your VPS server to install the missing Python packages:

### Step 1: Check Python Environment
```bash
# SSH into VPS
ssh root@your-vps-ip

# Navigate to project directory
cd /var/www/pdf-generator

# Check if virtual environment exists
ls -la venv/

# Check current Python path being used
which python
python --version
```

### Step 2: Activate Virtual Environment (If Exists)
```bash
# If venv directory exists, activate it
source venv/bin/activate

# Check if pandas is installed
pip list | grep pandas

# If not found, pandas is missing
```

### Step 3: Install Missing Python Dependencies
```bash
# Install pandas and other required packages
pip install pandas openpyxl reportlab Pillow requests segno qrcode

# Or if you have requirements.txt
pip install -r requirements.txt

# Verify installation
pip list | grep -E "pandas|openpyxl|reportlab|Pillow|requests"
```

### Step 4: Test Python Script Directly
```bash
# Test if SPH_Fresh.py can run now
python SPH_Fresh.py --help

# Should not show "ModuleNotFoundError" anymore
```

### Step 5: Restart Server
```bash
# Restart PM2 processes
pm2 restart all

# Check logs
pm2 logs --lines 10
```

## 📋 **Complete Python Setup (If No Virtual Environment)**

If you don't have a virtual environment, create one:

```bash
# On VPS - Create virtual environment
cd /var/www/pdf-generator
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install all required packages
pip install pandas==2.0.3 openpyxl==3.1.2 reportlab==4.0.4 Pillow==10.0.0 requests==2.31.0 segno==1.5.2 qrcode==7.4.2 sib-api-v3-sdk==7.6.0 python-dotenv==1.0.0

# Verify installation
pip list

# Test Python script
python SPH_Fresh.py --help
```

## 🔧 **Update server.js to Use Virtual Environment**

The server.js needs to use the virtual environment Python:

```bash
# Check current Python path detection in server.js
grep -A 10 "getPythonPath" server.js

# The code should automatically detect venv/bin/python
# If not, you may need to update the path
```

## 📋 **Alternative: System-wide Installation**

If virtual environment doesn't work:

```bash
# Install packages system-wide
sudo apt update
sudo apt install python3-pip
pip3 install pandas openpyxl reportlab Pillow requests segno qrcode sib-api-v3-sdk python-dotenv

# Test
python3 -c "import pandas; print('pandas works!')"
```

## ✅ **Verify Fix Works**

After installing dependencies:

```bash
# Test Python imports
python -c "import pandas, openpyxl, reportlab; print('All modules imported successfully!')"

# Test PDF generation script
python SPH_Fresh.py --help

# Check PM2 logs for errors
pm2 logs --lines 20

# Should not see "ModuleNotFoundError" anymore
```

## 🎯 **Quick Fix Summary**

The issue is **missing Python packages**, not route conflicts. Run these commands:

```bash
# On VPS
cd /var/www/pdf-generator
source venv/bin/activate  # if venv exists
pip install pandas openpyxl reportlab Pillow requests segno qrcode
pm2 restart all
```

Then test PDF generation - it should work!

## 📊 **Create requirements.txt for Future**

To prevent this issue in the future:

```bash
# On VPS - Create requirements.txt
cat > requirements.txt << 'EOF'
pandas==2.0.3
openpyxl==3.1.2
reportlab==4.0.4
Pillow==10.0.0
requests==2.31.0
segno==1.5.2
qrcode==7.4.2
sib-api-v3-sdk==7.6.0
python-dotenv==1.0.0
EOF

# Install from requirements
pip install -r requirements.txt
```

## 🚨 **If Virtual Environment Issues Persist**

If you can't get the virtual environment working:

```bash
# Delete old venv and create fresh one
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Test
python -c "import pandas; print('Success!')"
```

---

**The route conflict was a red herring - the real issue is missing Python dependencies on your VPS server.**