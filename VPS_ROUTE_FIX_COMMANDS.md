# VPS Route Fix Commands - Check and Deploy

## 🚨 Issue: PDF Generation Still Failing with 500 Errors on VPS

The route fix needs to be deployed to your VPS server. Here are the exact commands to run.

## 📋 Step 1: Check Current VPS Status

SSH into your VPS and run these commands:

```bash
# SSH into VPS
ssh root@your-vps-ip

# Navigate to project directory
cd /var/www/pdf-generator

# Check current Git status
git status
git log --oneline -3

# Check if server.js contains the fix
grep -n "Skip ALL paths that should not be handled by short URL redirect" server.js

# If the above command returns nothing, the fix is NOT deployed
```

## 📋 Step 2: Deploy the Route Fix to VPS

```bash
# On VPS - Pull the latest changes
git pull origin main

# Check if the fix is now present
grep -n "Skip ALL paths that should not be handled by short URL redirect" server.js

# Should return something like:
# 2576:  // Skip ALL paths that should not be handled by short URL redirect

# Check server.js modification time
ls -la server.js
```

## 📋 Step 3: Restart Server on VPS

```bash
# Check current PM2 processes
pm2 list

# Restart all processes
pm2 restart all

# Or restart specific process (replace with your actual process name)
pm2 restart pdf-generator

# Check process status
pm2 status

# Check recent logs
pm2 logs --lines 20
```

## 📋 Step 4: Verify Fix on VPS

```bash
# Test API endpoints directly on VPS
curl -I http://localhost:3001/api/status
curl -I http://localhost:3001/api/templates

# Both should return "HTTP/1.1 200 OK", not 500

# Test from outside (replace with your domain)
curl -I https://your-domain.com/api/status
curl -I https://your-domain.com/api/templates
```

## 📋 Step 5: Check VPS Server Logs

```bash
# Check PM2 logs for errors
pm2 logs --lines 50

# Check for route conflicts in logs
pm2 logs | grep -i "redirect\|route\|500"

# Check Nginx logs if needed
sudo tail -f /var/log/nginx/error.log
```

## 🔧 Alternative Fix: Temporarily Disable Short URL Handler

If the route fix doesn't work, temporarily disable the short URL handler:

```bash
# On VPS - Edit server.js
nano server.js

# Find this line (around line 2573):
# app.get('/:shortId', (req, res, next) => {

# Comment it out by adding // at the beginning:
# // app.get('/:shortId', (req, res, next) => {

# Also comment out the entire function until the closing });

# Save and restart
pm2 restart all
```

## 🚨 Emergency Commands (If Server Won't Start)

```bash
# Kill all Node processes
pm2 delete all

# Start fresh
pm2 start server.js --name pdf-generator

# Check status
pm2 status

# Save PM2 configuration
pm2 save
```

## 📊 Quick Diagnostic Script for VPS

Create this script on your VPS:

```bash
# On VPS - Create diagnostic script
cat > vps_diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== VPS Server Diagnostic ==="
echo "1. Checking Git status..."
git status
echo ""
echo "2. Checking for route fix..."
grep -n "Skip ALL paths" server.js || echo "Route fix NOT found"
echo ""
echo "3. Checking PM2 processes..."
pm2 list
echo ""
echo "4. Testing API endpoints..."
curl -s -I http://localhost:3001/api/status | head -1
curl -s -I http://localhost:3001/api/templates | head -1
echo ""
echo "5. Recent logs..."
pm2 logs --lines 10
EOF

# Make it executable
chmod +x vps_diagnostic.sh

# Run it
./vps_diagnostic.sh
```

## 🎯 Expected Results After Fix

After running these commands, you should see:

1. **Git pull** shows the route fix is now present
2. **grep command** finds the "Skip ALL paths" comment
3. **PM2 restart** completes successfully  
4. **curl tests** return "200 OK" not "500 Internal Server Error"
5. **PDF generation** works without 500 errors

## 📞 If Issues Persist

If you still get 500 errors after these steps:

```bash
# Check detailed error logs
pm2 logs pdf-generator --lines 100

# Check if Python virtual environment is working
source venv/bin/activate
python --version
pip list | grep pandas

# Test Python script directly
python SPH_Fresh.py --help
```

## 🚀 Quick Fix Summary

**Most likely issue**: The route fix hasn't been deployed to VPS yet.

**Quick solution**:
```bash
ssh root@your-vps-ip
cd /var/www/pdf-generator  
git pull origin main
pm2 restart all
```

Then test PDF generation again - it should work without 500 errors.

---

**Note**: Replace `your-vps-ip` and `your-domain.com` with your actual VPS IP and domain name.