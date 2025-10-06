#!/bin/bash

# PDF Generator VPS Deployment Script
# Run this script on your VPS to deploy the PDF Generator app

set -e  # Exit on any error

echo "🚀 Starting PDF Generator Deployment..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root or with sudo access
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
    print_warning "Not running as root. Will use sudo for system commands."
fi

# Step 1: System Information
print_status "Checking system resources..."
echo "Memory:"
free -h
echo ""
echo "Disk Space:"
df -h /
echo ""

# Step 2: Check existing services
print_status "Checking existing services..."
if pgrep -f streamlit > /dev/null; then
    print_status "Streamlit app is running ✓"
else
    print_warning "Streamlit app not detected"
fi

# Step 3: Install Node.js if needed
print_status "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js is installed: $NODE_VERSION"
else
    print_status "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | $SUDO bash -
    $SUDO apt-get install -y nodejs
    print_status "Node.js installed: $(node --version)"
fi

# Step 4: Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --user pandas openpyxl reportlab segno requests python-dotenv PyPDF2

# Step 5: Create directory structure
print_status "Setting up directory structure..."
cd /var/www
if [ -d "pdf-generator" ]; then
    print_warning "pdf-generator directory exists. Backing up..."
    $SUDO mv pdf-generator pdf-generator-backup-$(date +%Y%m%d-%H%M%S)
fi

$SUDO mkdir -p pdf-generator
$SUDO chown $USER:$USER pdf-generator
cd pdf-generator

# Step 6: Clone repository
print_status "Cloning repository..."
git clone https://github.com/Vkdel001/lettergeneration.git .

# Step 7: Install dependencies
print_status "Installing Node.js dependencies..."
npm install

# Step 8: Create environment file
print_status "Creating environment file..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Brevo API Configuration
BREVO_API_KEY=your-actual-brevo-api-key-here

# Email Configuration
DEFAULT_SENDER_EMAIL=noreply@nic.mu
DEFAULT_SENDER_NAME=NIC Insurance

# ZwennPay Configuration
ZWENNPAY_MERCHANT_ID=151
EOF
    print_warning "Please edit .env file with your actual API keys!"
    print_warning "Run: nano /var/www/pdf-generator/.env"
fi

# Step 9: Create fonts directory
print_status "Setting up fonts directory..."
mkdir -p fonts
print_warning "Please upload your Cambria font files to: /var/www/pdf-generator/fonts/"
print_warning "Required files: cambria.ttf and cambriab.ttf"

# Step 10: Build application
print_status "Building application..."
npm run build

# Step 11: Install PM2 if needed
print_status "Setting up PM2..."
if ! command -v pm2 &> /dev/null; then
    $SUDO npm install -g pm2
    print_status "PM2 installed"
else
    print_status "PM2 already installed"
fi

# Step 12: Create PM2 ecosystem file
print_status "Creating PM2 configuration..."
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

# Step 13: Configure firewall
print_status "Configuring firewall..."
$SUDO ufw allow 8501 2>/dev/null || true
$SUDO ufw allow 3001 2>/dev/null || true
$SUDO ufw allow 80 2>/dev/null || true
$SUDO ufw allow 443 2>/dev/null || true

# Step 14: Test server startup
print_status "Testing server startup..."
timeout 10s npm run server &
SERVER_PID=$!
sleep 5

if curl -s http://localhost:3001/api/status > /dev/null; then
    print_status "Server test successful ✓"
else
    print_warning "Server test failed - check configuration"
fi

# Kill test server
kill $SERVER_PID 2>/dev/null || true

# Step 15: Create startup script
print_status "Creating startup script..."
cat > start-apps.sh << 'EOF'
#!/bin/bash
cd /var/www/pdf-generator
pm2 start ecosystem.config.js
pm2 save
EOF

chmod +x start-apps.sh

# Step 16: Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh << 'EOF'
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
netstat -tlnp | grep -E ':(8501|3001)' 2>/dev/null || echo "No services found on ports 8501 or 3001"
EOF

chmod +x monitor.sh

# Final instructions
echo ""
echo "🎉 Deployment Setup Complete!"
echo "==============================="
echo ""
print_status "Next steps:"
echo "1. Edit environment file: nano /var/www/pdf-generator/.env"
echo "2. Upload font files to: /var/www/pdf-generator/fonts/"
echo "   - cambria.ttf"
echo "   - cambriab.ttf"
echo "3. Start applications: cd /var/www/pdf-generator && ./start-apps.sh"
echo "4. Check status: pm2 status"
echo "5. View logs: pm2 logs"
echo ""
print_status "Access URLs (after starting):"
echo "- Streamlit App: http://$(curl -s ifconfig.me):8501"
echo "- PDF Generator: http://$(curl -s ifconfig.me):3001"
echo ""
print_status "Monitoring:"
echo "- Run: ./monitor.sh"
echo "- Logs: pm2 logs"
echo ""
print_warning "Don't forget to:"
echo "- Add your real Brevo API key to .env"
echo "- Upload the required font files"
echo "- Test both applications after starting"
echo ""
echo "🚀 Ready to launch!"