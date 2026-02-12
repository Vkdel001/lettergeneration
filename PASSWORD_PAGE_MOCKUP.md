# Password Entry Page - Visual Mockup

**Document Purpose:** Visual reference for password entry page implementation  
**Security Level:** Maximum - Zero information disclosure

---

## 🔒 Password Entry Page (Before Authentication)

### **Desktop View:**

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                                                                │
│                      [NICL Logo - 120px]                       │
│                                                                │
│                                                                │
│              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                 │
│                                                                │
│                   🔒 Secure Access Required                    │
│                                                                │
│                   Dear Valued Customer,                        │
│                                                                │
│              To access the details, please provide            │
│              your National ID number as password.             │
│                                                                │
│              ┌──────────────────────────────────────┐         │
│              │                                      │         │
│              │  Enter Your National ID (No spaces) │         │
│              │                                      │         │
│              │  ┌────────────────────────────────┐ │         │
│              │  │                                │ │         │
│              │  │  [________________________]   │ │         │
│              │  │                                │ │         │
│              │  │  Example: A1234567890123       │ │         │
│              │  │                                │ │         │
│              │  │    [  Access Document  ]       │ │         │
│              │  │                                │ │         │
│              │  └────────────────────────────────┘ │         │
│              │                                      │         │
│              └──────────────────────────────────────┘         │
│                                                                │
│                                                                │
│              ℹ️  Your National ID is required for security     │
│                                                                │
│              📞 Need help? Call 602-3315                       │
│                                                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### **Mobile View:**

```
┌──────────────────────────┐
│                          │
│    [NICL Logo - 80px]    │
│                          │
│  ━━━━━━━━━━━━━━━━━━━━━  │
│                          │
│  🔒 Secure Access        │
│                          │
│  Dear Valued Customer,   │
│                          │
│  To access the details,  │
│  please provide your     │
│  National ID number as   │
│  password.               │
│                          │
│  ┌────────────────────┐  │
│  │ National ID:       │  │
│  │ (No spaces)        │  │
│  │                    │  │
│  │ [______________]   │  │
│  │                    │  │
│  │ Example:           │  │
│  │ A1234567890123     │  │
│  │                    │  │
│  │ [ Access Document ]│  │
│  └────────────────────┘  │
│                          │
│  ℹ️  NIC required for    │
│     security             │
│                          │
│  📞 Help: 602-3315       │
│                          │
└──────────────────────────┘
```

---

## ❌ Error States

### **Invalid NIC (Attempts Remaining):**

```
┌────────────────────────────────────────────────────────────────┐
│                      [NICL Logo]                               │
│                                                                │
│                   🔒 Secure Access Required                    │
│                                                                │
│                   Dear Valued Customer,                        │
│                                                                │
│              ┌──────────────────────────────────────┐         │
│              │  ❌ Invalid National ID               │         │
│              │                                      │         │
│              │  9 attempts remaining                │         │
│              └──────────────────────────────────────┘         │
│                                                                │
│              ┌──────────────────────────────────────┐         │
│              │  Enter Your National ID (No spaces) │         │
│              │  [________________________]          │         │
│              │                                      │         │
│              │    [  Try Again  ]                   │         │
│              └──────────────────────────────────────┘         │
│                                                                │
│              📞 Need help? Call 602-3315                       │
└────────────────────────────────────────────────────────────────┘
```

### **Locked Out (After 10 Failed Attempts):**

```
┌────────────────────────────────────────────────────────────────┐
│                      [NICL Logo]                               │
│                                                                │
│                   🔒 Access Temporarily Locked                 │
│                                                                │
│                   Dear Valued Customer,                        │
│                                                                │
│              ┌──────────────────────────────────────┐         │
│              │  ⏱️  Too many failed attempts         │         │
│              │                                      │         │
│              │  Please try again in 28 minutes     │         │
│              │                                      │         │
│              │  For immediate assistance:           │         │
│              │  📞 Call 602-3315                    │         │
│              └──────────────────────────────────────┘         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### **Expired Link:**

```
┌────────────────────────────────────────────────────────────────┐
│                      [NICL Logo]                               │
│                                                                │
│                   ⚠️  Link Expired                             │
│                                                                │
│                   Dear Valued Customer,                        │
│                                                                │
│              ┌──────────────────────────────────────┐         │
│              │  This link has expired.              │         │
│              │                                      │         │
│              │  Please contact NICL for assistance: │         │
│              │  📞 602-3315                         │         │
│              │  📧 nicarlife@nicl.mu                │         │
│              └──────────────────────────────────────┘         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### **Invalid Link:**

```
┌────────────────────────────────────────────────────────────────┐
│                      [NICL Logo]                               │
│                                                                │
│                   ⚠️  Invalid Link                             │
│                                                                │
│                   Dear Valued Customer,                        │
│                                                                │
│              ┌──────────────────────────────────────┐         │
│              │  This link is not valid.             │         │
│              │                                      │         │
│              │  Please contact NICL for assistance: │         │
│              │  📞 602-3315                         │         │
│              │  📧 nicarlife@nicl.mu                │         │
│              └──────────────────────────────────────┘         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## ✅ After Successful Authentication

**Only AFTER successful NIC verification, the customer sees:**

```
┌────────────────────────────────────────────────────────────────┐
│  [📄 Download PDF]  [🖨️ Print]                                 │
│                                                                │
│                      [NICL Logo]                               │
│              National Insurance Co. Ltd                        │
│              ━━━━━━━━━━━━━━━━━━━━━━━━━━                       │
│                                                                │
│  12-February-2026                                              │
│                                                                │
│  MR JOHN DOE                                                   │
│  123 MAIN STREET                                               │
│  PORT LOUIS                                                    │
│                                                                │
│  RE: ARREARS ON YOUR LIFE INSURANCE POLICY                    │
│                                                                │
│  Dear Mr Doe,                                                  │
│                                                                │
│  [Full letter content with policy details, QR code, etc.]     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Principles

### **CRITICAL: Zero Information Disclosure**

**Before Authentication (Password Page):**
- ❌ NO policy number
- ❌ NO customer name
- ❌ NO customer address
- ❌ NO policy details
- ❌ NO expiry date
- ❌ NO amount owed
- ❌ NO hints about customer identity
- ✅ ONLY generic greeting: "Dear Valued Customer"
- ✅ ONLY NICL logo and branding
- ✅ ONLY password prompt

**After Authentication (Letter Viewer):**
- ✅ Full customer details
- ✅ Policy information
- ✅ Letter content
- ✅ QR code
- ✅ Download options

### **Why This Matters:**

1. **Privacy Protection:** If link is accidentally shared, no data is exposed
2. **Regulatory Compliance:** Meets GDPR/POPIA requirements
3. **Security Best Practice:** No information leakage before authentication
4. **Customer Trust:** Shows NICL takes data protection seriously
5. **Prevents Social Engineering:** Attackers can't verify whose letter it is

---

## 📝 Implementation Notes

### **HTML Structure:**

```html
<!-- Password Entry Page - NO customer data loaded -->
<!DOCTYPE html>
<html>
<head>
  <title>NICL - Secure Access</title>
</head>
<body>
  <div class="password-container">
    <img src="/api/logo" alt="NICL Logo" />
    <h1>🔒 Secure Access Required</h1>
    <p>Dear Valued Customer,</p>
    <p>To access the details, please provide your National ID number as password.</p>
    
    <form id="nicForm" method="POST" action="/api/verify-letter-access">
      <input type="hidden" name="uniqueId" value="{{uniqueId}}" />
      <label>Enter Your National ID (No spaces):</label>
      <input type="text" name="nic" placeholder="A1234567890123" required />
      <button type="submit">Access Document</button>
    </form>
    
    <p class="help">ℹ️ Your National ID is required for security</p>
    <p class="help">📞 Need help? Call 602-3315</p>
  </div>
</body>
</html>
```

### **Server Logic:**

```javascript
app.get('/letter/:uniqueId', (req, res) => {
  const { uniqueId } = req.params;
  
  // Check session FIRST - do NOT load letter data yet
  const session = validateSession(req.cookies.nicl_letter_session);
  
  if (session && session.uniqueId === uniqueId) {
    // Valid session - NOW load letter data and show viewer
    const letterData = loadLetterData(uniqueId);
    return res.send(generateLetterViewerHTML(letterData));
  } else {
    // No valid session - show password page
    // IMPORTANT: Do NOT load letter data, do NOT pass customer info
    return res.send(generatePasswordEntryHTML(uniqueId));
  }
});
```

---

## ✅ Approval Checklist

- [ ] Password page shows NO customer information
- [ ] Generic greeting only: "Dear Valued Customer"
- [ ] NO policy number displayed
- [ ] NO customer name displayed
- [ ] NO expiry date displayed
- [ ] Error messages are generic
- [ ] Help contact information included
- [ ] Mobile-responsive design
- [ ] Accessible (screen reader friendly)
- [ ] Clear password format instructions

---

**END OF MOCKUP DOCUMENT**
