# NICL Letter Generation System - Project Handover Documentation
## Part 3: Operations & Maintenance

---

## 🔄 Daily Operations

### Starting/Stopping the Application

```bash
# SSH into VPS
ssh root@your-vps-ip

# Navigate to project
cd /var/www/pdf-generator

# Check status
pm2 status

# Start application
pm2 start ecosystem.config.js

# Stop application
pm2 stop pdf-generator

# Restart application
pm2 restart pdf-generator

# View logs
pm2 logs pdf-generator

# View last 50 lines
pm2 logs pdf-generator --lines 50
```

### Monitoring Application Health

```bash
# Check PM2 process
pm2 status

# Check memory usage
pm2 monit

# Check server resources
htop

# Check disk space
df -h

# Check Nginx status
sudo systemctl status nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/arrears.access.log
sudo tail -f /var/log/nginx/arrears.error.log
```

---

## 📊 Common Operations

### Processing Large Batches (5000+ Records)

**Best Practices**:
1. **Check disk space** before processing
2. **Monitor memory** during generation
3. **Use email notifications** for completion alerts
4. **Process during off-peak hours** if possible

```bash
# Check available disk space
df -h /var/www/pdf-generator

# Monitor memory during processing
watch -n 5 free -h

# Check PM2 logs for progress
pm2 logs pdf-generator --lines 100
```

### Cleaning Up Old Files

```bash
# Navigate to project
cd /var/www/pdf-generator

# List output folders by size
du -sh output_*/ | sort -h

# Remove old output folders (older than 30 days)
find . -maxdepth 1 -name "output_*" -type d -mtime +30 -exec rm -rf {} \;

# Clean temp uploads
rm -rf temp_uploads/*

# Clean old letter links (older than 60 days)
find letter_links/ -type d -mtime +60 -exec rm -rf {} \;
```

### Updating the Application

```bash
# SSH into VPS
ssh root@your-vps-ip
cd /var/www/pdf-generator

# Backup current version
sudo cp -r /var/www/pdf-generator /var/www/pdf-generator-backup-$(date +%Y%m%d)

# Pull latest changes
git pull origin main

# Update Node dependencies (if package.json changed)
npm install

# Update Python dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Rebuild frontend
npm run build

# Restart application
pm2 restart pdf-generator

# Check logs for errors
pm2 logs pdf-generator --lines 20
```

---

## 🚨 Troubleshooting Guide

### Issue 1: PDF Generation Fails with 500 Error

**Symptoms**: 
- Frontend shows "Python script execution failed"
- PM2 logs show "ModuleNotFoundError"

**Diagnosis**:
```bash
# Check if venv has required packages
source venv/bin/activate
python -c "import pandas, reportlab, fitz; print('All OK')"
```

**Solution**:
```bash
# Reinstall Python packages
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Restart server
pm2 restart pdf-generator
```

### Issue 2: QR Codes Missing in Combined PDFs

**Symptoms**:
- Individual PDFs have QR codes
- Combined PDF shows empty space where QR should be
- Adobe shows "error exists on this page"

**Diagnosis**:
```bash
# Check if PyMuPDF is installed
source venv/bin/activate
python -c "import fitz; print('PyMuPDF OK')" || echo "PyMuPDF MISSING"
```

**Solution**:
```bash
# Install PyMuPDF
source venv/bin/activate
pip install PyMuPDF
deactivate

# Restart server
pm2 restart pdf-generator

# Regenerate combined PDF
```

**Root Cause**: The combine_pdfs.py script requires PyMuPDF for proper image preservation. PyPDF2 corrupts QR codes during merging.

### Issue 3: Short URLs Not Working

**Symptoms**:
- nicl.ink/abc123 returns 404
- Short URL redirect fails

**Diagnosis**:
```bash
# Check if url_mappings.json exists
ls -la url_mappings.json

# Check Nginx configuration
sudo nginx -t

# Check PM2 logs
pm2 logs pdf-generator | grep -i redirect
```

**Solution**:
```bash
# Verify Nginx is routing to Node.js
curl -I http://localhost:3001/health

# Check url_mappings.json format
cat url_mappings.json | python -m json.tool

# Restart services
pm2 restart pdf-generator
sudo systemctl reload nginx
```

### Issue 4: Email Notifications Not Sending

**Symptoms**:
- PDF generation completes but no email received
- PM2 logs show email errors

**Diagnosis**:
```bash
# Check environment variables
cat .env | grep BREVO

# Test email system
source venv/bin/activate
python test_email_system.py your-email@example.com
```

**Solution**:
```bash
# Verify Brevo API key is correct
nano .env
# Update BREVO_API_KEY

# Restart application
pm2 restart pdf-generator

# Test again
source venv/bin/activate
python test_email_system.py your-email@example.com
```

### Issue 5: Application Won't Start

**Symptoms**:
- PM2 shows "errored" status
- Server logs show startup errors

**Diagnosis**:
```bash
# Check PM2 logs
pm2 logs pdf-generator --lines 50

# Check if port 3001 is in use
sudo lsof -i :3001

# Check Node.js version
node --version
```

**Solution**:
```bash
# Kill process on port 3001 (if needed)
sudo kill -9 $(sudo lsof -t -i:3001)

# Delete PM2 process and restart fresh
pm2 delete pdf-generator
pm2 start ecosystem.config.js

# Check status
pm2 status
```

### Issue 6: SSL Certificate Expired

**Symptoms**:
- Browser shows "Your connection is not private"
- Certificate expired warning

**Diagnosis**:
```bash
# Check certificate status
sudo certbot certificates
```

**Solution**:
```bash
# Renew certificates
sudo certbot renew

# Reload Nginx
sudo systemctl reload nginx

# Verify renewal
sudo certbot certificates
```

---

## 🔧 Maintenance Tasks

### Weekly Maintenance

```bash
# 1. Check disk space
df -h

# 2. Check application logs for errors
pm2 logs pdf-generator --lines 100 | grep -i error

# 3. Check Nginx logs for issues
sudo tail -100 /var/log/nginx/arrears.error.log

# 4. Verify SSL certificates
sudo certbot certificates

# 5. Check system updates
sudo apt update
sudo apt list --upgradable
```

### Monthly Maintenance

```bash
# 1. Clean old output folders
find /var/www/pdf-generator -name "output_*" -type d -mtime +30 -exec rm -rf {} \;

# 2. Clean old letter links
find /var/www/pdf-generator/letter_links -type d -mtime +60 -exec rm -rf {} \;

# 3. Update system packages
sudo apt update && sudo apt upgrade -y

# 4. Check PM2 logs size
du -sh /var/log/pdf-generator/

# 5. Rotate logs if needed
pm2 flush

# 6. Test backup script
sudo /usr/local/bin/backup-pdf-generator.sh
```

### Quarterly Maintenance

```bash
# 1. Update Node.js dependencies
cd /var/www/pdf-generator
npm outdated
npm update

# 2. Update Python dependencies
source venv/bin/activate
pip list --outdated
pip install --upgrade pip
deactivate

# 3. Review and update documentation

# 4. Test disaster recovery procedure

# 5. Review and clean up old backups
ls -lh /var/backups/pdf-generator/
```

---

## 📈 Performance Optimization

### Monitoring Performance

```bash
# Check Node.js memory usage
pm2 monit

# Check Python script execution time
pm2 logs pdf-generator | grep "Processing time"

# Check Nginx response times
sudo tail -100 /var/log/nginx/arrears.access.log | awk '{print $NF}' | sort -n
```

### Optimization Tips

1. **For Large Batches (5000+ records)**:
   - Increase PM2 memory limit if needed
   - Process during off-peak hours
   - Monitor disk I/O

2. **For Faster PDF Generation**:
   - Ensure venv is on SSD
   - Use PyMuPDF for combining (faster than PyPDF2)
   - Batch QR code API calls

3. **For Better Response Times**:
   - Enable Nginx caching for static files
   - Use gzip compression
   - Optimize frontend bundle size

---

## 🔐 Security Best Practices

### Regular Security Tasks

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Check for security updates
sudo apt list --upgradable | grep -i security

# 3. Review Nginx access logs for suspicious activity
sudo tail -1000 /var/log/nginx/arrears.access.log | grep -E "404|500|403"

# 4. Check firewall status
sudo ufw status

# 5. Verify SSL certificates are valid
sudo certbot certificates
```

### Security Checklist

- [ ] .env file has restricted permissions (600)
- [ ] Firewall is enabled and configured
- [ ] SSL certificates are valid and auto-renewing
- [ ] PM2 is running as non-root user (if possible)
- [ ] Nginx security headers are configured
- [ ] Regular backups are running
- [ ] System packages are up to date
- [ ] Application dependencies are up to date

---

**Continue to Part 4: API Reference & Troubleshooting**