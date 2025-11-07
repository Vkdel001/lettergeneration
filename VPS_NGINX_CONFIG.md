# VPS Nginx Configuration for Large File Uploads

## Issue: 413 Payload Too Large Error

When uploading large Excel files (10,000+ rows), you may encounter a 413 error. This is due to Nginx's default upload size limit.

## Solution: Update Nginx Configuration

### 1. Edit Nginx Configuration

```bash
# SSH to VPS
ssh root@your-vps-ip

# Edit the Nginx configuration for your site
sudo nano /etc/nginx/sites-available/pdf-generator
# OR if using default config
sudo nano /etc/nginx/nginx.conf
```

### 2. Add Client Max Body Size

Add this line inside the `http` block or `server` block:

```nginx
# Inside http block (applies to all sites)
http {
    ...
    client_max_body_size 50M;
    ...
}

# OR inside server block (applies to specific site)
server {
    listen 80;
    server_name your-domain.com;
    
    # Allow uploads up to 50MB
    client_max_body_size 50M;
    
    location / {
        ...
    }
    
    location /api/ {
        proxy_pass http://localhost:3001;
        ...
    }
}
```

### 3. Test and Reload Nginx

```bash
# Test configuration for syntax errors
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx

# OR restart if reload doesn't work
sudo systemctl restart nginx
```

### 4. Verify the Change

```bash
# Check Nginx status
sudo systemctl status nginx

# Test upload with curl
curl -X POST -F "excelFile=@large_file.xlsx" http://your-domain.com/api/generate-pdfs
```

## Complete Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name pdf.niclmauritius.site;
    
    # Increase upload size limit to 50MB
    client_max_body_size 50M;
    
    # Increase timeouts for long-running PDF generation
    proxy_connect_timeout 21600;
    proxy_send_timeout 21600;
    proxy_read_timeout 21600;
    send_timeout 21600;
    
    # Frontend
    location / {
        root /var/www/pdf-generator/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for long-running processes
        proxy_connect_timeout 21600s;
        proxy_send_timeout 21600s;
        proxy_read_timeout 21600s;
    }
}
```

## Troubleshooting

### Still Getting 413 Error?

1. **Check if Nginx config was reloaded:**
   ```bash
   sudo systemctl status nginx
   ```

2. **Check Nginx error logs:**
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Verify client_max_body_size is set:**
   ```bash
   sudo nginx -T | grep client_max_body_size
   ```

4. **Try increasing the limit further:**
   ```nginx
   client_max_body_size 100M;  # Increase to 100MB
   ```

### Getting Timeout Errors?

If uploads work but processing times out:

1. **Increase proxy timeouts in Nginx** (see example above)
2. **Check PM2 logs:**
   ```bash
   pm2 logs pdf-generator --lines 50
   ```

3. **Monitor Python process:**
   ```bash
   ps aux | grep python
   ```

## Summary of Changes

1. **Node.js server.js**: Increased to 50MB
2. **Nginx**: Set `client_max_body_size 50M`
3. **Nginx timeouts**: Set to 6 hours for long processing

After these changes, you should be able to upload Excel files with 10,000+ rows without issues.
