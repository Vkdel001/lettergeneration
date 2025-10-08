#!/bin/bash
# Check Process and System Limits on VPS
# Run this to see if the process is being killed due to resource limits

echo "🔍 Checking Process and System Limits"
echo "====================================="

echo ""
echo "1. Memory Usage:"
echo "---------------"
free -h
echo ""
echo "Memory usage by PDF generator:"
ps aux | grep "node.*server.js" | grep -v grep

echo ""
echo "2. System Limits:"
echo "----------------"
echo "Current user limits:"
ulimit -a

echo ""
echo "3. System-wide limits:"
echo "---------------------"
echo "Max processes:"
cat /proc/sys/kernel/pid_max
echo ""
echo "Max open files:"
cat /proc/sys/fs/file-max

echo ""
echo "4. OOM Killer Logs (Out of Memory):"
echo "-----------------------------------"
echo "Checking for recent OOM kills:"
dmesg | grep -i "killed process" | tail -5 || echo "No recent OOM kills found"

echo ""
echo "5. System Load:"
echo "--------------"
uptime
echo ""
echo "CPU and memory info:"
top -bn1 | head -20

echo ""
echo "6. Disk Space:"
echo "-------------"
df -h

echo ""
echo "7. PM2 Process Info:"
echo "-------------------"
pm2 monit --no-interaction | head -20

echo ""
echo "8. Check for Process Restarts:"
echo "-----------------------------"
echo "PM2 restart count:"
pm2 list | grep pdf-generator

echo ""
echo "9. System Journal Errors:"
echo "------------------------"
echo "Recent system errors:"
journalctl --since "1 hour ago" --priority=err --no-pager | tail -10 || echo "No recent errors"

echo ""
echo "🎯 Analysis:"
echo "==========="
echo "If you see:"
echo "- High memory usage: Process might be killed due to memory limits"
echo "- OOM kills: System is running out of memory"
echo "- High restart count: Process is being killed and restarted"
echo "- System errors: Check for hardware/system issues"