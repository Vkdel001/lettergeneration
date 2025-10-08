#!/bin/bash
# VPS Timeout Debugging Script
# Run this on your VPS to check all timeout configurations

echo "🔍 VPS Timeout Configuration Debug"
echo "=================================="

echo ""
echo "1. Git Status & Recent Commits:"
echo "------------------------------"
git log --oneline -3
echo ""
git status

echo ""
echo "2. Server.js Timeout Configuration:"
echo "----------------------------------"
echo "Searching for 21600000 (6 hours in ms):"
grep -n "21600000" server.js || echo "❌ 6-hour timeout NOT found in server.js"

echo ""
echo "Searching for timeout comments:"
grep -n -i "6 hour" server.js || echo "❌ 6-hour comments NOT found"

echo ""
echo "3. PM2 Configuration:"
echo "--------------------"
pm2 show pdf-generator 2>/dev/null || echo "❌ PM2 process not found"

echo ""
echo "4. System Limits:"
echo "----------------"
echo "Process limits:"
ulimit -a | grep -E "(time|cpu)"

echo ""
echo "5. Network Timeouts:"
echo "-------------------"
echo "Checking nginx configuration (if exists):"
if [ -f /etc/nginx/sites-enabled/apps ]; then
    echo "Nginx config found:"
    grep -n -i timeout /etc/nginx/sites-enabled/apps || echo "No nginx timeouts found"
else
    echo "No nginx config found"
fi

echo ""
echo "6. Node.js Process Check:"
echo "------------------------"
ps aux | grep node | grep -v grep

echo ""
echo "7. Current Server Status:"
echo "------------------------"
curl -I http://localhost:3001/api/status 2>/dev/null || echo "❌ Server not responding"

echo ""
echo "8. Environment Variables:"
echo "------------------------"
echo "NODE_ENV: ${NODE_ENV:-not set}"
echo "PORT: ${PORT:-not set}"

echo ""
echo "🎯 Recommendations:"
echo "==================="
echo "1. If 21600000 not found in server.js: git pull origin main"
echo "2. If PM2 shows old config: pm2 restart pdf-generator"
echo "3. If nginx has timeouts: update nginx config"
echo "4. Check PM2 logs: pm2 logs pdf-generator --lines 50"