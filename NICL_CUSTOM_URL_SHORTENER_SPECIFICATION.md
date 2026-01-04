# NICL Custom URL Shortener Implementation Guide
## Using nicl.ink Domain for SMS Links

**Document Version**: 1.0  
**Created**: December 29, 2024  
**Domain**: nicl.ink (purchased from Namecheap)  
**Purpose**: Replace TinyURL with custom branded short URLs for SMS notifications

---

## 📋 **Project Overview**

### **Objective**
Implement a custom URL shortening service using the newly purchased `nicl.ink` domain to replace TinyURL for SMS notifications, providing:
- Shorter URLs than current TinyURL (23 vs 28 characters)
- Professional NICL branding
- No third-party landing pages
- Full control over redirect behavior

### **Current vs Proposed URLs**
```
Current TinyURL:    https://tinyurl.com/2csxdvfw           (28 characters)
Current Direct:     https://niclmauritius.site/letter/abc  (52 characters)
Proposed Short:     https://nicl.ink/abc123               (23 characters)
```

**Benefits**: 5 characters shorter than TinyURL, 29 characters shorter than direct URLs

---

## 🎯 **Phase 1: Domain Setup & URL Redirection (PRIORITY 1)**

### **1.1 DNS Configuration**

#### **At Namecheap (Domain Registrar)**
```
Domain: nicl.ink
DNS Records to Add:

A Record:
- Host: @
- Value: [YOUR_VPS_IP_ADDRESS]
- TTL: Automatic

A Record:
- Host: www
- Value: [YOUR_VPS_IP_ADDRESS]  
- TTL: Automatic

CNAME Record (Optional):
- Host: *
- Value: nicl.ink
- TTL: Automatic
```

#### **Verification Commands**
```bash
# Test DNS propagation
nslookup nicl.ink
dig nicl.ink

# Test from different locations
ping nicl.ink
```

### **1.2 SSL Certificate Setup**

#### **Using Let's Encrypt (Recommended)**
```bash
# SSH into VPS
ssh root@your-vps-ip

# Install certbot if not already installed
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificate for nicl.ink
sudo certbot --nginx -d nicl.ink -d www.nicl.ink

# Verify certificate
sudo certbot certificates
```

### **1.3 Nginx Configuration**

#### **Create Virtual Host for nicl.ink**
```bash
# Create new Nginx site configuration
sudo nano /etc/nginx/sites-available/nicl.ink
```

#### **Basic Nginx Configuration**
```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name nicl.ink www.nicl.ink;
    return 301 https://nicl.ink$request_uri;
}

# HTTPS server for redirects
server {
    listen 443 ssl http2;
    server_name nicl.ink www.nicl.ink;
    
    # SSL Configuration (managed by certbot)
    ssl_certificate /etc/letsencrypt/live/nicl.ink/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nicl.ink/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Root directory (for static files if needed)
    root /var/www/nicl-redirect;
    index index.html;
    
    # Main redirect handler
    location / {
        # For now, redirect all traffic to main site
        # This will be replaced with custom redirect service later
        return 301 https://niclmauritius.site$request_uri;
    }
    
    # Health check endpoint
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
    
    # Logs
    access_log /var/log/nginx/nicl.ink.access.log;
    error_log /var/log/nginx/nicl.ink.error.log;
}
```

#### **Enable the Site**
```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/nicl.ink /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### **1.4 Testing Basic Redirect**

#### **Test Commands**
```bash
# Test HTTP redirect to HTTPS
curl -I http://nicl.ink

# Test HTTPS response
curl -I https://nicl.ink

# Test with browser
# Visit https://nicl.ink - should redirect to https://niclmauritius.site
```

#### **Expected Results**
- `http://nicl.ink` → redirects to `https://nicl.ink`
- `https://nicl.ink` → redirects to `https://niclmauritius.site`
- SSL certificate valid and trusted
- No browser security warnings

---

## 🏗️ **Phase 2: Custom Redirect Service Implementation**

### **2.1 Architecture Overview**

```
SMS Link: https://nicl.ink/abc123
    ↓
Nginx: nicl.ink (port 443)
    ↓
Node.js Redirect Service (port 3002)
    ↓
Lookup: abc123 → https://niclmauritius.site/letter/7e89984128160d9b
    ↓
HTTP 301 Redirect to target URL
```

### **2.2 Storage Options**

#### **Option A: JSON File Storage (Simple)**
```json
// /var/www/nicl-redirect/urls.json
{
  "abc123": {
    "url": "https://niclmauritius.site/letter/7e89984128160d9b",
    "created": "2024-12-29T10:00:00Z",
    "clicks": 0,
    "expires": "2025-01-29T10:00:00Z"
  }
}
```

#### **Option B: SQLite Database (Scalable)**
```sql
CREATE TABLE short_urls (
    short_id VARCHAR(10) PRIMARY KEY,
    long_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    click_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1
);
```

### **2.3 Short ID Generation Strategy**

#### **Format Options**
- **Alphanumeric**: `abc123` (6 characters, case-insensitive)
- **Base62**: `aBc123` (6 characters, case-sensitive, more combinations)
- **Custom**: `nicl001` (branded format)

#### **Collision Handling**
- Check for existing ID before assignment
- Retry with new ID if collision detected
- Maximum 5 retry attempts

---

## 📝 **Phase 3: Integration with SMS Generation**

### **3.1 Files to Modify**

#### **Primary File: `generate_sms_links.py`**
**Current Function:**
```python
def create_short_url(long_url):
    response = requests.get(f"https://tinyurl.com/api-create.php?url={long_url}")
    return response.text.strip()
```

**Proposed Change:**
```python
def create_short_url(long_url):
    # Generate unique short ID
    short_id = generate_short_id()
    
    # Store mapping (JSON file or database)
    store_url_mapping(short_id, long_url)
    
    # Return short URL
    return f"https://nicl.ink/{short_id}"
```

#### **Secondary File: `server.js`**
**New Endpoint Addition:**
```javascript
// Add redirect service endpoint
app.get('/redirect/:shortId', (req, res) => {
    const longUrl = lookupShortUrl(req.params.shortId);
    if (longUrl && !isExpired(longUrl)) {
        incrementClickCount(req.params.shortId);
        res.redirect(301, longUrl.url);
    } else {
        res.status(404).send('Link not found or expired');
    }
});
```

### **3.2 URL Mapping Storage**

#### **JSON File Approach**
```javascript
// Helper functions for JSON storage
function storeUrlMapping(shortId, longUrl) {
    const mapping = {
        url: longUrl,
        created: new Date().toISOString(),
        expires: new Date(Date.now() + 30*24*60*60*1000).toISOString(), // 30 days
        clicks: 0,
        active: true
    };
    
    const urls = loadUrlMappings();
    urls[shortId] = mapping;
    saveUrlMappings(urls);
}
```

---

## 🔧 **Phase 4: Production Deployment**

### **4.1 Deployment Checklist**

#### **Pre-Deployment**
- [ ] DNS propagation complete (24-48 hours)
- [ ] SSL certificate installed and valid
- [ ] Basic redirect working (nicl.ink → niclmauritius.site)
- [ ] Nginx configuration tested
- [ ] Backup current SMS generation system

#### **Deployment Steps**
1. **Deploy redirect service** (separate Node.js process)
2. **Update Nginx configuration** to proxy to redirect service
3. **Modify `generate_sms_links.py`** to use custom URLs
4. **Test with small batch** of SMS links
5. **Monitor redirect success rate**
6. **Full rollout** after successful testing

#### **Rollback Plan**
- Revert `generate_sms_links.py` to use TinyURL
- Keep redirect service running for existing short URLs
- Monitor for any broken links

### **4.2 Monitoring & Maintenance**

#### **Health Checks**
```bash
# Check redirect service status
curl -I https://nicl.ink/health

# Check SSL certificate expiry
sudo certbot certificates

# Monitor redirect success rate
tail -f /var/log/nginx/nicl.ink.access.log
```

#### **Analytics Tracking**
- Click count per short URL
- Most accessed links
- Geographic distribution (from Nginx logs)
- Error rate monitoring

---

## 📊 **Impact Analysis**

### **Files Modified**
| File | Change Type | Risk Level | Description |
|------|-------------|------------|-------------|
| `generate_sms_links.py` | Function replacement | LOW | Replace TinyURL API call |
| `server.js` | New endpoint | LOW | Add redirect lookup endpoint |
| Nginx config | New virtual host | MEDIUM | New domain configuration |

### **Infrastructure Changes**
| Component | Change | Risk Level |
|-----------|--------|------------|
| DNS | New A records | LOW |
| SSL | New certificate | LOW |
| Nginx | New virtual host | MEDIUM |
| Node.js | New redirect service | MEDIUM |

### **Benefits vs Risks**

#### **Benefits**
- ✅ 5 characters shorter than TinyURL
- ✅ Professional NICL branding
- ✅ No third-party dependencies
- ✅ No landing pages
- ✅ Full control over redirects
- ✅ Analytics capabilities

#### **Risks**
- ⚠️ Additional infrastructure to maintain
- ⚠️ DNS propagation delays
- ⚠️ SSL certificate renewal
- ⚠️ Redirect service uptime dependency

---

## 🚀 **Implementation Timeline**

### **Week 1: Domain Setup**
- **Day 1-2**: DNS configuration and propagation
- **Day 3**: SSL certificate setup
- **Day 4**: Basic Nginx redirect configuration
- **Day 5**: Testing and verification

### **Week 2: Service Development**
- **Day 1-2**: Develop redirect service
- **Day 3**: Integration with SMS generation
- **Day 4**: Testing with sample URLs
- **Day 5**: Production deployment preparation

### **Week 3: Deployment & Testing**
- **Day 1**: Deploy to production
- **Day 2-3**: Small batch testing
- **Day 4**: Full rollout
- **Day 5**: Monitoring and optimization

---

## 📞 **Support & Troubleshooting**

### **Common Issues**

#### **DNS Not Resolving**
```bash
# Check DNS propagation
dig nicl.ink @8.8.8.8
nslookup nicl.ink

# Wait 24-48 hours for full propagation
```

#### **SSL Certificate Issues**
```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

#### **Redirect Not Working**
```bash
# Check Nginx status
sudo systemctl status nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t
```

### **Emergency Contacts**
- **Domain Registrar**: Namecheap support
- **VPS Provider**: Your VPS provider support
- **SSL Issues**: Let's Encrypt community forum

---

## 📋 **Next Steps**

### **Immediate Actions Required**
1. **Configure DNS** at Namecheap to point nicl.ink to VPS IP
2. **Wait for DNS propagation** (24-48 hours)
3. **Set up SSL certificate** using Let's Encrypt
4. **Configure basic Nginx redirect** for testing
5. **Verify redirect functionality** before proceeding to Phase 2

### **Success Criteria for Phase 1**
- [ ] `https://nicl.ink` loads without SSL warnings
- [ ] `https://nicl.ink` redirects to `https://niclmauritius.site`
- [ ] DNS resolves correctly from multiple locations
- [ ] SSL certificate is valid and trusted

---

**Document Status**: Ready for Phase 1 Implementation  
**Approval Required**: DNS configuration and basic redirect setup  
**No Code Changes**: This phase requires only infrastructure setup