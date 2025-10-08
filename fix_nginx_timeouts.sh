#!/bin/bash
# Fix Nginx Timeouts for Long PDF Processing
# Run this on your VPS if you're using Nginx

echo "🔧 Fixing Nginx Timeouts for 6-Hour PDF Processing"
echo "=================================================="

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx not found - skipping nginx timeout fix"
    exit 0
fi

echo "✅ Nginx found - checking configuration..."

# Backup existing config
if [ -f /etc/nginx/sites-enabled/apps ]; then
    sudo cp /etc/nginx/sites-enabled/apps /etc/nginx/sites-enabled/apps.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
fi

# Check current nginx config
echo ""
echo "Current nginx timeout settings:"
if [ -f /etc/nginx/sites-enabled/apps ]; then
    grep -n -i timeout /etc/nginx/sites-enabled/apps || echo "No timeout settings found"
else
    echo "No nginx config found at /etc/nginx/sites-enabled/apps"
fi

echo ""
echo "🎯 To fix nginx timeouts, add these lines to your nginx config:"
echo ""
echo "server {"
echo "    # ... existing config ..."
echo "    "
echo "    # PDF Generator location with 6-hour timeouts"
echo "    location /pdf-generator/ {"
echo "        proxy_pass http://localhost:3001/;"
echo "        proxy_set_header Host \$host;"
echo "        proxy_set_header X-Real-IP \$remote_addr;"
echo "        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "        proxy_set_header X-Forwarded-Proto \$scheme;"
echo "        "
echo "        # 6-hour timeouts for large PDF processing"
echo "        proxy_connect_timeout 21600s;"
echo "        proxy_send_timeout 21600s;"
echo "        proxy_read_timeout 21600s;"
echo "        send_timeout 21600s;"
echo "    }"
echo "}"
echo ""
echo "After updating nginx config, run:"
echo "sudo nginx -t"
echo "sudo systemctl reload nginx"