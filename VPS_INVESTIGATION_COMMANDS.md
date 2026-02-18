# VPS Investigation - Why Did Working App Suddenly Break?

## 🤔 **You're Right - Something Changed**

If this was a working application, Python dependencies don't just disappear. Let's investigate what changed.

## 🔍 **Possible Causes**

1. **Python path changed** - server.js might be using wrong Python
2. **Virtual environment deactivated** - venv path might be broken
3. **System update** - VPS might have been updated
4. **Git pull changed Python path** - new code might use different Python
5. **PM2 restart changed environment** - environment variables lost

## 📋 **Investigation Commands for VPS**

### Step 1: Check What Python is Being Used
```bash
# SSH into VPS
ssh root@your-vps-ip
cd /var/www/pdf-generator

# Check what Python server.js is trying to use
grep -A 20 "getPythonPath" server.js

# Check if venv exists and works
ls -la venv/
source venv/bin/activate
which python
python -c "import pandas; print('pandas available in venv')"
```

### Step 2: Check System Python vs VPS Python
```bash
# Check system Python
which python3
python3 -c "import pandas; print('pandas in system python')" 2>/dev/null || echo "pandas NOT in system python"

# Check if venv Python has pandas
venv/bin/python -c "import pandas; print('pandas in venv python')" 2>/dev/null || echo "pandas NOT in venv python"

# Check what Python PM2 is using
pm2 logs --lines 50 | grep -i python
```

### Step 3: Check Recent Changes
```bash
# Check recent Git changes
git log --oneline -10

# Check when server.js was last modified
ls -la server.js

# Check PM2 process details
pm2 show pdf-generator
```

### Step 4: Check Environment Variables
```bash
# Check if PM2 lost environment variables
pm2 env 0  # or whatever your process ID is

# Check if PYTHON_PATH or similar changed
env | grep -i python
```

## 🔧 **Most Likely Causes & Quick Fixes**

### Cause 1: Server.js Using Wrong Python Path
The `getPythonPath()` function in server.js might be detecting the wrong Python.

**Check:**
```bash
# See what Python path is being detected
node -e "
const fs = require('fs');
const path = require('path');
const getPythonPath = () => {
  const venvPath = path.join(__dirname, 'venv', 'bin', 'python');
  if (fs.existsSync(venvPath)) {
    console.log('Using VPS virtual environment:', venvPath);
    return venvPath;
  }
  console.log('Using system python (local development)');
  return 'python';
};
console.log('Detected Python path:', getPythonPath());
"
```

**Fix if wrong:**
```bash
# Force server.js to use venv Python
# Edit the getPythonPath function to always use venv
```

### Cause 2: Virtual Environment Corrupted
**Check:**
```bash
# Test venv directly
venv/bin/python -c "import sys; print(sys.executable)"
venv/bin/pip list | grep pandas
```

**Fix if corrupted:**
```bash
# Don't recreate venv - just reinstall packages
source venv/bin/activate
pip install --force-reinstall pandas openpyxl reportlab Pillow requests
```

### Cause 3: PM2 Environment Issue
**Check:**
```bash
# Check PM2 environment
pm2 show pdf-generator | grep -A 10 "env:"
```

**Fix:**
```bash
# Restart PM2 with fresh environment
pm2 delete pdf-generator
pm2 start server.js --name pdf-generator
```

## 🚨 **Emergency Diagnostic Script**

Run this on VPS to see exactly what's happening:

```bash
cat > debug_python_issue.sh << 'EOF'
#!/bin/bash
echo "=== Python Path Investigation ==="
echo "1. Current directory: $(pwd)"
echo "2. VPS venv exists: $(ls -la venv/ 2>/dev/null && echo 'YES' || echo 'NO')"
echo "3. VPS venv python works: $(venv/bin/python --version 2>/dev/null || echo 'BROKEN')"
echo "4. VPS venv has pandas: $(venv/bin/python -c 'import pandas; print("YES")' 2>/dev/null || echo 'NO')"
echo "5. System python: $(which python3)"
echo "6. System python has pandas: $(python3 -c 'import pandas; print("YES")' 2>/dev/null || echo 'NO')"
echo "7. What server.js detects:"

node -e "
const fs = require('fs');
const path = require('path');
const getPythonPath = () => {
  const venvPath = path.join(__dirname, 'venv', 'bin', 'python');
  if (fs.existsSync(venvPath)) {
    console.log('   VPS venv detected:', venvPath);
    return venvPath;
  }
  if (process.env.VIRTUAL_ENV) {
    const envPython = path.join(process.env.VIRTUAL_ENV, 'bin', 'python');
    if (fs.existsSync(envPython)) {
      console.log('   ENV venv detected:', envPython);
      return envPython;
    }
  }
  console.log('   Using system python');
  return 'python';
};
const pythonPath = getPythonPath();
console.log('   Final Python path:', pythonPath);
"

echo "8. PM2 process info:"
pm2 show pdf-generator | grep -E "(script|cwd|env)"
EOF

chmod +x debug_python_issue.sh
./debug_python_issue.sh
```

## 🎯 **Most Likely Fix**

Based on the error, I suspect the issue is that **server.js is not using the venv Python** anymore. 

**Quick fix:**
```bash
# On VPS - Force server.js to use the correct Python
# Check if venv has pandas
source venv/bin/activate
pip list | grep pandas

# If pandas is there, the issue is Python path detection
# Restart PM2 from the correct directory
cd /var/www/pdf-generator
pm2 delete pdf-generator
pm2 start server.js --name pdf-generator
```

## 🔍 **What to Look For**

The debug script will show:
- ✅ If venv exists and has pandas
- ✅ What Python path server.js is detecting  
- ✅ If PM2 is running from the right directory
- ✅ If environment variables are correct

**Most likely**: The `getPythonPath()` function is returning `'python'` (system python) instead of `venv/bin/python`, and system python doesn't have pandas installed.

Run the debug script first - it will tell us exactly what's wrong!