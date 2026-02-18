# SMS Link Feature - Critical Issues and Fixes

## 🚨 **IDENTIFIED ISSUES**

### **Issue 1: Wrong Letter Format Used**
- **Problem**: Loaded `output_sph.xlsx` but letter viewer shows MED format instead of SPH format
- **Impact**: Incorrect letter content, wrong template applied
- **Root Cause**: Letter viewer uses generic template instead of template-specific content

### **Issue 2: Letter Viewer Design Mismatch**
- **Problem**: Letter viewer appearance doesn't match actual PDF design
- **Impact**: Inconsistent branding, unprofessional appearance
- **Root Cause**: HTML template doesn't replicate PDF styling accurately

### **Issue 3: Missing QR Code in Letter Viewer**
- **Problem**: QR code for payments is not embedded in the letter viewer
- **Impact**: CRITICAL - Customers cannot make payments via mobile banking
- **Root Cause**: QR code generation not implemented in letter viewer

### **Issue 4: Unnecessary Password Protection**
- **Problem**: Downloaded PDF from letter viewer is password-protected
- **Impact**: Poor user experience - customer already authenticated via SMS link
- **Root Cause**: Using protected PDF instead of unprotected version

---

## 🔧 **DETAILED FIXES**

### **Fix 1: Template-Specific Letter Content**

The letter viewer currently uses a generic template. We need to make it template-aware and use the correct format based on the original template used.

**Current Problem:**
```javascript
// Generic content for all templates
<p><strong>RE: ARREARS ON YOUR LIFE INSURANCE POLICY</strong></p>
```

**Required Fix:**
```javascript
// Template-specific content
{letterData.templateType === 'SPH' && (
  <p><strong>RE: ARREARS ON YOUR LIFE INSURANCE POLICY</strong></p>
)}
{letterData.templateType === 'MED' && (
  <p><strong>RE: FIRST NOTICE ARREARS ON HEALTH INSURANCE POLICY</strong></p>
)}
```

### **Fix 2: Accurate PDF-Matching Design**

The letter viewer needs to replicate the exact PDF appearance with:
- Correct NICL logo positioning
- Matching fonts (Cambria)
- Exact spacing and layout
- Professional letterhead design
- Proper color scheme

### **Fix 3: QR Code Integration**

**Critical Fix Required:**
1. Generate QR code for each customer during SMS link creation
2. Store QR code data in JSON file
3. Display QR code in letter viewer
4. Ensure QR code works with mobile banking apps

### **Fix 4: Unprotected PDF Download**

Change PDF download to use unprotected version since customer is already authenticated via SMS link.

---

## 🛠️ **IMPLEMENTATION PLAN**

### **Phase 1: Fix Template Detection (HIGH PRIORITY)**

**File to Update:** `generate_sms_links.py`

Add template-specific content extraction:

```python
def extract_letter_content_by_template(row, template_type):
    """Extract template-specific letter content"""
    
    base_content = extract_letter_data(row, index, template_type)
    
    if template_type == 'SPH':
        base_content.update({
            "subject": "RE: ARREARS ON YOUR LIFE INSURANCE POLICY",
            "letterType": "Life Insurance",
            "productType": "SPH",
            "bodyIntro": "At NIC, we value the trust you have placed in us to protect what matters most— your financial future & that of your loved ones."
        })
    elif template_type == 'MED_SPH' or template_type == 'MED_JPH':
        base_content.update({
            "subject": "RE: FIRST NOTICE ARREARS ON HEALTH INSURANCE POLICY",
            "letterType": "Health Insurance", 
            "productType": "MED",
            "bodyIntro": "We are writing to you with regards to the aforementioned Insurance Policy and we have noticed that there remains an outstanding amount due."
        })
    elif template_type == 'JPH':
        base_content.update({
            "subject": "RE: ARREARS ON YOUR LIFE INSURANCE POLICY",
            "letterType": "Life Insurance",
            "productType": "JPH", 
            "bodyIntro": "At NIC, we value the trust you have placed in us to protect what matters most— your financial future & that of your loved ones."
        })
    elif template_type == 'Company':
        base_content.update({
            "subject": "RE: ARREARS ON YOUR COMPANY INSURANCE POLICY",
            "letterType": "Company Insurance",
            "productType": "Company",
            "bodyIntro": "We are writing to inform you about the outstanding premium on your company insurance policy."
        })
    
    return base_content
```

### **Phase 2: Add QR Code Generation (CRITICAL)**

**File to Update:** `generate_sms_links.py`

Add QR code generation during SMS link creation:

```python
def generate_qr_code_for_customer(row, policy_no, mobile_no, nic, arrears_amount):
    """Generate QR code for customer payment"""
    try:
        payload = {
            "MerchantId": 151,
            "SetTransactionAmount": False,
            "TransactionAmount": 0,
            "SetConvenienceIndicatorTip": False,
            "ConvenienceIndicatorTip": 0,
            "SetConvenienceFeeFixed": False,
            "ConvenienceFeeFixed": 0,
            "SetConvenienceFeePercentage": False,
            "ConvenienceFeePercentage": 0,
            "SetAdditionalBillNumber": True,
            "AdditionalRequiredBillNumber": False,
            "AdditionalBillNumber": str(policy_no.replace('/', '.')),
            "SetAdditionalMobileNo": True,
            "AdditionalRequiredMobileNo": False,
            "AdditionalMobileNo": str(mobile_no),
            "SetAdditionalStoreLabel": False,
            "AdditionalRequiredStoreLabel": False,
            "AdditionalStoreLabel": "",
            "SetAdditionalLoyaltyNumber": False,
            "AdditionalRequiredLoyaltyNumber": False,
            "AdditionalLoyaltyNumber": "",
            "SetAdditionalReferenceLabel": False,
            "AdditionalRequiredReferenceLabel": False,
            "AdditionalReferenceLabel": "",
            "SetAdditionalCustomerLabel": True,
            "AdditionalRequiredCustomerLabel": False,
            "AdditionalCustomerLabel": str(customer_name),
            "SetAdditionalTerminalLabel": False,
            "AdditionalRequiredTerminalLabel": False,
            "AdditionalTerminalLabel": "",
            "SetAdditionalPurposeTransaction": True,
            "AdditionalRequiredPurposeTransaction": False,
            "AdditionalPurposeTransaction": str(nic)
        }
        
        response = requests.post(
            "https://api.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR",
            headers={"accept": "text/plain", "Content-Type": "application/json"},
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            qr_data = str(response.text).strip()
            if qr_data and qr_data.lower() not in ('null', 'none', 'nan'):
                return qr_data
        
        return None
        
    except Exception as e:
        print(f"[SMS] QR generation failed for {policy_no}: {e}")
        return None
```

### **Phase 3: Update Letter Viewer HTML (HIGH PRIORITY)**

**File to Update:** `server.js` - `generateLetterViewerHTML` function

Complete rewrite to match PDF design:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NICL - ${letterData.letterType} Arrears Notice</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: 'Cambria', 'Times New Roman', serif; 
      line-height: 1.4; 
      color: #000; 
      background-color: #fff;
      padding: 20px;
      font-size: 11pt;
    }
    .container { 
      max-width: 210mm; 
      margin: 0 auto; 
      background: white; 
      padding: 50px 50px 60px 50px; 
      min-height: 297mm;
      position: relative;
    }
    
    /* Header with logo positioning matching PDF */
    .header { 
      position: relative;
      margin-bottom: 80px;
    }
    .logo { 
      position: absolute;
      top: 5px;
      right: 0;
      width: 120px;
      height: auto;
    }
    
    /* Date positioning */
    .date { 
      text-align: left; 
      margin-bottom: 15px; 
      font-weight: bold;
      font-size: 11pt;
    }
    
    /* Address block */
    .address { 
      margin-bottom: 20px; 
      line-height: 1.2;
    }
    .address p { 
      margin-bottom: 4px; 
      font-weight: bold;
      font-size: 11pt;
      text-transform: uppercase;
    }
    
    /* Subject line */
    .subject { 
      font-weight: bold; 
      margin: 20px 0; 
      font-size: 11pt;
      text-decoration: underline;
    }
    
    /* Salutation */
    .salutation { 
      margin-bottom: 15px; 
      font-size: 11pt;
    }
    
    /* Body content */
    .content { 
      margin-bottom: 15px; 
      text-align: justify;
      font-size: 11pt;
      line-height: 1.4;
    }
    
    /* Policy table matching PDF exactly */
    .policy-table { 
      width: 100%; 
      border-collapse: collapse; 
      margin: 20px 0; 
      font-size: 10pt;
    }
    .policy-table th, .policy-table td { 
      border: 1px solid #000; 
      padding: 8px; 
      text-align: center; 
      vertical-align: middle;
    }
    .policy-table th { 
      background-color: #f8f9fa; 
      font-weight: bold;
      font-size: 10pt;
    }
    
    /* QR Code section */
    .qr-section { 
      text-align: center; 
      margin: 30px 0; 
    }
    .qr-code { 
      width: 100px; 
      height: 100px; 
      margin: 10px auto;
    }
    .maucas-logo {
      width: 110px;
      height: auto;
      margin-bottom: 10px;
    }
    .zwenn-logo {
      width: 50px;
      height: auto;
      margin-top: 10px;
    }
    
    /* Footer */
    .footer { 
      position: absolute;
      bottom: 30px;
      left: 50px;
      right: 50px;
      text-align: center; 
      font-size: 10pt; 
      color: #666;
    }
    
    /* Action buttons */
    .actions { 
      text-align: center; 
      margin: 30px 0; 
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 1000;
    }
    .btn { 
      display: inline-block; 
      padding: 8px 16px; 
      margin: 0 5px; 
      background-color: #0066cc; 
      color: white; 
      text-decoration: none; 
      border-radius: 4px; 
      font-size: 12pt;
      font-weight: bold;
    }
    .btn:hover { 
      background-color: #0052a3; 
    }
    
    /* Print styles */
    @media print {
      .actions { display: none; }
      .container { padding: 20px; }
      body { font-size: 10pt; }
    }
    
    /* Mobile responsive */
    @media (max-width: 600px) {
      .container { padding: 20px; }
      .actions { position: static; margin-top: 20px; }
      .btn { display: block; margin: 5px 0; }
    }
  </style>
</head>
<body>
  <div class="actions">
    <a href="/api/download-pdf-unprotected/${letterData.id}" class="btn" target="_blank">
      📄 Download PDF
    </a>
    <a href="javascript:window.print()" class="btn">
      🖨️ Print
    </a>
  </div>

  <div class="container">
    <div class="header">
      <img src="/api/logo" alt="NICL Logo" class="logo" />
    </div>

    <div class="date">${letterData.date}</div>

    <div class="address">
      ${letterData.address.map(line => `<p>${line.toUpperCase()}</p>`).join('')}
    </div>

    <div class="subject">${letterData.subject}</div>

    <div class="salutation">${letterData.salutation}</div>

    <div class="content">
      <p>${letterData.bodyIntro}</p>
      
      ${letterData.templateType === 'SPH' || letterData.templateType === 'JPH' ? `
        <p>We are writing to remind you that your life insurance policy shows a <strong>premium amount in arrears as shown below:</strong></p>
      ` : `
        <p>The total amount of arrears as detailed in the table below is <strong>${letterData.policyDetails.arrearsAmount}</strong>.</p>
      `}
    </div>

    <table class="policy-table">
      <thead>
        <tr>
          <th>Policy No.</th>
          <th>Payment Frequency</th>
          <th>Premium Amount</th>
          <th>Total Premium in Arrears</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>${letterData.policyDetails.policyNo}</td>
          <td>${letterData.policyDetails.frequency}</td>
          <td>${letterData.policyDetails.premium}</td>
          <td><strong>${letterData.policyDetails.arrearsAmount}</strong></td>
        </tr>
      </tbody>
    </table>

    ${letterData.qrCodeData ? `
      <div class="qr-section">
        <p>For your convenience, you may settle payments via QR code:</p>
        <img src="/api/maucas-logo" alt="MauCAS" class="maucas-logo" />
        <div>
          <canvas id="qrcode" class="qr-code"></canvas>
        </div>
        <img src="/api/zwenn-logo" alt="ZwennPay" class="zwenn-logo" />
      </div>
      
      <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
      <script>
        QRCode.toCanvas(document.getElementById('qrcode'), '${letterData.qrCodeData}', {
          width: 100,
          margin: 2,
          color: {
            dark: '#000000',
            light: '#FFFFFF'
          }
        });
      </script>
    ` : ''}

    <div class="content">
      ${letterData.templateType === 'SPH' || letterData.templateType === 'JPH' ? `
        <p>Keeping your policy up to date ensures:</p>
        <ul style="margin: 15px 0 15px 30px;">
          <li><strong>Continuity of Protection:</strong> You and your family remain covered.</li>
          <li><strong>Growth of Your Savings:</strong> Every premium contributes to long-term savings.</li>
          <li><strong>Peace of Mind:</strong> Financial safety net remains intact.</li>
        </ul>
      ` : `
        <p>Maintaining timely payments ensures uninterrupted coverage and access to your benefits.</p>
      `}
      
      <p>For assistance, contact us on +230 602 3315.</p>
      
      <p><em>If you have already settled this amount, please accept our thanks and disregard this reminder.</em></p>
    </div>

    <div class="footer">
      <p><strong>NIC - Serving you, Serving the Nation</strong></p>
      <p><em>This is a computer generated statement and requires no signature</em></p>
      <p>📱 This letter expires on: <strong>${expiryDate}</strong> | 📧 nicarlife@nicl.mu | ☎️ 602-3315</p>
    </div>
  </div>
</body>
</html>
```

### **Phase 4: Add Logo and Asset Endpoints**

**File to Update:** `server.js`

Add endpoints to serve logos:

```javascript
// Serve NICL logo
app.get('/api/logo', (req, res) => {
  const logoPath = path.join(__dirname, 'NICLOGO2.jpg');
  if (fs.existsSync(logoPath)) {
    res.sendFile(logoPath);
  } else {
    res.status(404).send('Logo not found');
  }
});

// Serve MauCAS logo
app.get('/api/maucas-logo', (req, res) => {
  const logoPath = path.join(__dirname, 'maucas2.jpeg');
  if (fs.existsSync(logoPath)) {
    res.sendFile(logoPath);
  } else {
    res.status(404).send('MauCAS logo not found');
  }
});

// Serve ZwennPay logo
app.get('/api/zwenn-logo', (req, res) => {
  const logoPath = path.join(__dirname, 'zwennPay.jpg');
  if (fs.existsSync(logoPath)) {
    res.sendFile(logoPath);
  } else {
    res.status(404).send('ZwennPay logo not found');
  }
});

// Serve unprotected PDF (no password)
app.get('/api/download-pdf-unprotected/:uniqueId', (req, res) => {
  // Same logic as download-pdf but use unprotected folder
  const { uniqueId } = req.params;
  
  // Find letter data and get unprotected PDF path
  // ... implementation similar to existing download-pdf but from unprotected folder
});
```

---

## 🚀 **IMPLEMENTATION PRIORITY**

### **CRITICAL (Fix Immediately):**
1. ✅ **QR Code Integration** - Customers need payment functionality
2. ✅ **Template-Specific Content** - Correct letter format
3. ✅ **Unprotected PDF Download** - Remove password requirement

### **HIGH (Fix Soon):**
1. ✅ **PDF-Matching Design** - Professional appearance
2. ✅ **Logo Integration** - Proper branding
3. ✅ **Mobile Responsiveness** - Customer accessibility

### **MEDIUM (Enhancement):**
1. ✅ **Print Optimization** - Better print layout
2. ✅ **Error Handling** - Graceful failures
3. ✅ **Performance** - Faster loading

---

## 🧪 **TESTING CHECKLIST**

After implementing fixes:

### **Template Detection Test:**
- [ ] Upload `output_sph.xlsx` → Should show SPH format
- [ ] Upload `output_jph.xlsx` → Should show JPH format  
- [ ] Upload `output_sph_med.xlsx` → Should show MED format

### **QR Code Test:**
- [ ] QR code appears in letter viewer
- [ ] QR code is scannable with mobile banking apps
- [ ] QR code contains correct payment data

### **Design Test:**
- [ ] Letter viewer matches PDF appearance
- [ ] NICL logo positioned correctly
- [ ] Fonts and spacing match PDF
- [ ] Mobile responsive design works

### **PDF Download Test:**
- [ ] Downloaded PDF is not password-protected
- [ ] PDF contains QR code
- [ ] PDF matches original generated PDF

---

## 📋 **IMPLEMENTATION STEPS**

1. **Update `generate_sms_links.py`** with QR code generation and template detection
2. **Update `server.js`** with new letter viewer HTML and logo endpoints
3. **Test with different templates** (SPH, JPH, MED, Company)
4. **Verify QR codes work** with mobile banking apps
5. **Test PDF downloads** are unprotected
6. **Validate design consistency** between PDF and web viewer

This comprehensive fix will resolve all identified issues and make the SMS Link feature production-ready with the correct template formats, QR code functionality, and professional appearance.