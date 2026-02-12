# SMS Link NIC Password Protection - Specification Document

**Document Version:** 1.0  
**Date:** February 12, 2026  
**Status:** Pending Approval  
**Author:** Kiro AI Assistant

---

## 📋 Executive Summary

This document specifies the implementation of National ID (NIC) password protection for SMS link letter access. This enhancement adds a security layer requiring customers to authenticate with their National ID before viewing arrears letters online or downloading PDFs.

---

## 🎯 Objectives

### **Primary Goals:**
1. Add NIC password authentication to letter viewer access
2. Use protected PDFs (password-protected with NIC)
3. Implement session management for authenticated access
4. Add failed attempt tracking and lockout mechanism
5. Maintain user experience while enhancing security

### **Security Requirements:**
- Two-factor authentication (SMS link + NIC password)
- Protection against brute force attacks
- Session-based access control
- Audit trail for access attempts

---

## 🔐 Security Specifications

### **Password Requirements:**
- **Password Type:** Full National ID (NIC)
- **Format:** Alphanumeric, no spaces allowed
- **Example:** `A1234567890123` or `1234567890123`
- **Case Sensitivity:** Case-insensitive (converted to uppercase)
- **Storage:** SHA256 hash only (never store plain text)

### **Information Disclosure Prevention:**
- **CRITICAL SECURITY REQUIREMENT:** Zero information disclosure before authentication
- **Password Entry Page:** Shows NO customer data, NO policy number, NO names
- **Generic Greeting Only:** "Dear Valued Customer"
- **Error Messages:** Generic, no specific details about customer or policy
- **Link Validation:** No hints about validity until after authentication
- **Rationale:** Prevents information leakage if link is shared or intercepted

### **Access Control:**
- **Failed Attempts Allowed:** 10 attempts
- **Lockout Duration:** 30 minutes
- **Session Duration:** Until browser closes (session cookie)
- **Session Storage:** Server-side with secure session tokens

### **PDF Protection:**
- **PDF Source:** Protected folder (not unprotected)
- **PDF Password:** Customer's full NIC (same as web access)
- **Password Format in PDF:** Full NIC without spaces

---

## 🔄 User Flow

### **Current Flow (Before Changes):**
```
Customer clicks SMS link
    ↓
Redirects to letter viewer URL
    ↓
HTML letter displayed immediately (no authentication)
    ↓
Download button → Unprotected PDF (no password)
```

### **New Flow (After Changes):**
```
Customer clicks SMS link
    ↓
Redirects to letter viewer URL
    ↓
Password Entry Page displayed
    ↓
Customer enters National ID
    ↓
Server validates NIC
    ├─ Valid → Create session → Show HTML letter viewer
    │           ↓
    │       Download button → Protected PDF (NIC password required)
    │
    └─ Invalid → Show error message
                 ↓
             Retry (up to 10 attempts)
                 ↓
             After 10 failed attempts → 30-minute lockout
```

---

## 📱 User Interface Changes

### **1. Password Entry Page**

**URL:** `/letter/:uniqueId` (without valid session)

**Page Content:**
```
┌─────────────────────────────────────────────────────┐
│              [NICL Logo]                            │
│                                                     │
│         🔒 Secure Access Required                  │
│                                                     │
│  Dear Valued Customer,                             │
│                                                     │
│  To access the details, please provide your        │
│  National ID number as password.                   │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Enter Your National ID (No spaces):          │ │
│  │ [_________________________________]           │ │
│  │                                               │ │
│  │ Example: A1234567890123                      │ │
│  │                                               │ │
│  │          [Access Document]                    │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ℹ️ Your National ID is required for security      │
│  📞 Need help? Call 602-3315                       │
└─────────────────────────────────────────────────────┘
```

**IMPORTANT SECURITY NOTE:**
- NO customer information displayed before authentication
- NO policy number shown
- NO customer name shown
- NO expiry date shown
- Generic greeting only: "Dear Valued Customer"

**Error States:**
- Invalid NIC: "Invalid National ID. X attempts remaining."
- Locked out: "Too many failed attempts. Please try again in X minutes."
- Expired link: "This link has expired. Please contact NICL at 602-3315."
- Invalid link: "Invalid access link. Please contact NICL at 602-3315."

**Security Features:**
- Zero information disclosure before authentication
- No hints about whose letter it is
- No policy details visible
- No expiry date shown
- Generic error messages (no specific details)

### **2. Letter Viewer Page (After Authentication)**

**URL:** `/letter/:uniqueId` (with valid session)

**Changes:**
- Same HTML viewer as current
- Download button now links to protected PDF
- Session indicator (optional): "✅ Authenticated"

### **3. Updated SMS Message**

**Current SMS:**
```
Dear Mr Doe, your NICL arrears notice is ready. 
View online: https://nicl.ink/abc123 
Valid for 30 days.
```

**New SMS:**
```
Dear Mr Doe, your NICL arrears notice is ready.
View: https://nicl.ink/abc123
Password: Your National ID (no spaces)
Valid 30 days | Help: 602-3315
```

---

## 🔧 Technical Implementation

### **1. Data Storage Changes**

**Letter JSON File Enhancement:**

Location: `letter_links/{output_folder}/{uniqueId}.json`

**New Fields Added:**
```json
{
  "id": "7e89984128160d9b",
  "policyNo": "00407/0094507",
  "customerName": "Mr John Doe",
  "mobileNo": "57123456",
  "nic": "A1234567890123",  // NEW: Plain NIC (for PDF password generation)
  "nicHash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  // NEW: SHA256 hash
  "pdfPath": "/output_sph_December2025/protected/001_00407_0094507_Mr_John_Doe.pdf",  // CHANGED: protected folder
  "accessAttempts": [],  // NEW: Track failed attempts
  "lockedUntil": null,   // NEW: Lockout timestamp
  // ... existing fields ...
}
```

**Access Attempts Tracking:**
```json
"accessAttempts": [
  {
    "timestamp": "2026-02-12T10:30:00Z",
    "success": false,
    "ipAddress": "192.168.1.1",
    "userAgent": "Mozilla/5.0..."
  }
]
```

### **2. Session Management**

**Session Storage:** Server-side in-memory Map (or Redis in production)

**Session Data Structure:**
```javascript
{
  sessionId: "sess_abc123def456",
  uniqueId: "7e89984128160d9b",
  authenticated: true,
  createdAt: "2026-02-12T10:30:00Z",
  expiresAt: null,  // Session cookie (expires on browser close)
  ipAddress: "192.168.1.1",
  userAgent: "Mozilla/5.0..."
}
```

**Session Cookie:**
- Name: `nicl_letter_session`
- HttpOnly: true
- Secure: true (HTTPS only in production)
- SameSite: Strict
- Expires: Session (browser close)

### **3. API Endpoints**

**New Endpoint: Password Verification**
```
POST /api/verify-letter-access

Request Body:
{
  "uniqueId": "7e89984128160d9b",
  "nic": "A1234567890123"
}

Response (Success):
{
  "success": true,
  "sessionId": "sess_abc123def456",
  "message": "Access granted"
}

Response (Invalid NIC):
{
  "success": false,
  "attemptsRemaining": 9,
  "message": "Invalid National ID. 9 attempts remaining."
}

Response (Locked Out):
{
  "success": false,
  "lockedUntil": "2026-02-12T11:00:00Z",
  "message": "Too many failed attempts. Please try again in 28 minutes."
}
```

**Modified Endpoint: Letter Viewer**
```
GET /letter/:uniqueId

Behavior:
- Check for valid session cookie
- If no session → Show password entry page (NO customer data)
- If valid session → Show letter viewer HTML (with customer data)
- If expired/invalid session → Show password entry page (NO customer data)

CRITICAL: Password entry page must NOT load or display any customer data
- Do NOT query letter JSON until after authentication
- Do NOT show policy number, name, or any identifying information
- Generic page only with NICL logo and password prompt
```

**Modified Endpoint: PDF Download**
```
GET /api/download-pdf/:uniqueId

Changes:
- Require valid session
- Use protected folder instead of unprotected
- PDF is password-protected with customer's NIC
```

### **4. Security Functions**

**NIC Validation:**
```javascript
function validateNIC(inputNIC, storedNICHash) {
  // Remove spaces, convert to uppercase
  const cleanNIC = inputNIC.replace(/\s/g, '').toUpperCase();
  
  // Generate hash
  const inputHash = crypto.createHash('sha256')
    .update(cleanNIC)
    .digest('hex');
  
  // Compare hashes
  return inputHash === storedNICHash;
}
```

**Lockout Check:**
```javascript
function checkLockout(letterData) {
  if (letterData.lockedUntil) {
    const now = new Date();
    const lockoutEnd = new Date(letterData.lockedUntil);
    
    if (now < lockoutEnd) {
      const minutesRemaining = Math.ceil((lockoutEnd - now) / 60000);
      return {
        locked: true,
        minutesRemaining: minutesRemaining
      };
    } else {
      // Lockout expired, reset
      letterData.lockedUntil = null;
      letterData.accessAttempts = [];
      return { locked: false };
    }
  }
  return { locked: false };
}
```

**Failed Attempt Tracking:**
```javascript
function recordFailedAttempt(letterData, ipAddress, userAgent) {
  letterData.accessAttempts.push({
    timestamp: new Date().toISOString(),
    success: false,
    ipAddress: ipAddress,
    userAgent: userAgent
  });
  
  // Check if lockout threshold reached
  if (letterData.accessAttempts.length >= 10) {
    letterData.lockedUntil = new Date(Date.now() + 30 * 60 * 1000).toISOString();
  }
  
  // Save updated letter data
  saveLetterData(letterData);
}
```

---

## 📂 Files to be Modified

### **Backend Files:**

#### **1. server.js** (Major Changes)
**Location:** `./server.js`

**Changes Required:**
- Add session management (Map or Redis)
- Add new endpoint: `POST /api/verify-letter-access`
- Modify endpoint: `GET /letter/:uniqueId` (add session check)
- Modify endpoint: `GET /api/download-pdf/:uniqueId` (use protected folder)
- Add function: `generatePasswordEntryHTML()`
- Add function: `validateNIC()`
- Add function: `checkLockout()`
- Add function: `recordFailedAttempt()`
- Add function: `createSession()`
- Add function: `validateSession()`
- Modify function: `generateLetterViewerHTML()` (add session info)

**Estimated Lines Changed:** ~300-400 lines

#### **2. generate_sms_links.py** (Moderate Changes)
**Location:** `./generate_sms_links.py`

**Changes Required:**
- Store NIC from Excel in letter JSON
- Generate NIC hash (SHA256)
- Change PDF path to use protected folder
- Initialize accessAttempts array
- Initialize lockedUntil field
- Update SMS message template

**Specific Changes:**
```python
# Line ~150: Extract NIC from Excel
nic = str(row.get('NIC', '')) if pd.notna(row.get('NIC', '')) else ''

# Line ~200: Generate NIC hash
import hashlib
nic_clean = nic.replace(' ', '').upper()
nic_hash = hashlib.sha256(nic_clean.encode()).hexdigest()

# Line ~250: Update letter data structure
letter_data.update({
    "nic": nic_clean,
    "nicHash": nic_hash,
    "accessAttempts": [],
    "lockedUntil": None
})

# Line ~300: Change PDF path
letter_data["pdfPath"] = f"/{output_folder}/protected/{pdf_filename}"

# Line ~350: Update SMS message
sms_text = f"Dear {name_for_sms}, your NICL arrears notice is ready. View: {short_url} Password: Your National ID (no spaces) Valid 30 days | Help: 602-3315"
```

**Estimated Lines Changed:** ~50-80 lines

### **Frontend Files:**

#### **3. No Frontend Changes Required**
The password entry page and letter viewer are server-rendered HTML, so no React component changes are needed.

### **Documentation Files:**

#### **4. SMS_LINK_FEATURE_SPECIFICATION.md** (Minor Update)
**Location:** `./SMS_LINK_FEATURE_SPECIFICATION.md`

**Changes Required:**
- Add section on NIC password authentication
- Update user flow diagrams
- Update SMS message examples

**Estimated Lines Changed:** ~20-30 lines

#### **5. SMS_CSV_GENERATION_EXPLAINED.md** (Minor Update)
**Location:** `./SMS_CSV_GENERATION_EXPLAINED.md`

**Changes Required:**
- Update SMS message format example
- Add note about NIC field requirement

**Estimated Lines Changed:** ~10-15 lines

### **Configuration Files:**

#### **6. No Configuration Changes Required**
No changes to `.env`, `package.json`, or other config files.

---

## 📊 Impact Analysis

### **Files Modified:**
| File | Type | Impact Level | Lines Changed |
|------|------|--------------|---------------|
| `server.js` | Backend | HIGH | ~300-400 |
| `generate_sms_links.py` | Backend | MEDIUM | ~50-80 |
| `SMS_LINK_FEATURE_SPECIFICATION.md` | Docs | LOW | ~20-30 |
| `SMS_CSV_GENERATION_EXPLAINED.md` | Docs | LOW | ~10-15 |

**Total Files Modified:** 4 files  
**Total Lines Changed:** ~380-525 lines

### **New Files Created:**
| File | Purpose |
|------|---------|
| `SMS_LINK_NIC_PASSWORD_SPECIFICATION.md` | This specification document |

### **Files NOT Modified:**
- All React components (`src/components/*.jsx`)
- All Python PDF generation scripts (`*_Fresh.py`)
- All test files (`test_*.py`)
- Configuration files (`.env`, `package.json`)
- Other documentation files

---

## 🧪 Testing Requirements

### **1. Unit Tests**

**NIC Validation:**
- Valid NIC formats
- Invalid NIC formats
- Case insensitivity
- Space handling
- Hash comparison

**Lockout Mechanism:**
- 10 failed attempts trigger lockout
- Lockout duration is 30 minutes
- Lockout resets after 30 minutes
- Successful login resets attempt counter

**Session Management:**
- Session creation
- Session validation
- Session expiry on browser close
- Invalid session handling

### **2. Integration Tests**

**Complete Flow:**
1. Generate SMS links with NIC data
2. Access letter URL without session
3. Enter invalid NIC (9 times)
4. Enter valid NIC on 10th attempt
5. View letter HTML
6. Download protected PDF
7. Close browser
8. Reopen link (should require password again)

**Lockout Flow:**
1. Enter invalid NIC 10 times
2. Verify lockout message
3. Wait 30 minutes
4. Verify access restored

### **3. Security Tests**

**Information Disclosure Prevention:**
- Verify password page shows NO customer data
- Verify password page shows NO policy number
- Verify password page shows NO customer name
- Verify password page shows NO expiry date
- Verify error messages are generic
- Verify link validation doesn't leak information

**Brute Force Protection:**
- Verify lockout after 10 attempts
- Verify lockout duration
- Verify attempt counter reset

**Session Security:**
- Verify session cookie is HttpOnly
- Verify session cookie is Secure (HTTPS)
- Verify session cannot be hijacked
- Verify session expires on browser close

**PDF Security:**
- Verify PDF requires password
- Verify PDF password is customer's NIC
- Verify PDF cannot be opened without password

### **4. User Acceptance Tests**

**Mobile Devices:**
- Test on iOS Safari
- Test on Android Chrome
- Test NIC entry on mobile keyboard
- Test PDF download on mobile

**Desktop Browsers:**
- Test on Chrome
- Test on Firefox
- Test on Edge
- Test on Safari

**Edge Cases:**
- Expired letter link
- Invalid unique ID
- Missing NIC in data
- Corrupted letter JSON

---

## 🚀 Deployment Plan

### **Phase 1: Development (Local)**
1. Implement changes in `server.js`
2. Implement changes in `generate_sms_links.py`
3. Test locally with sample data
4. Verify password entry page
5. Verify session management
6. Verify lockout mechanism

### **Phase 2: Testing (Staging)**
1. Deploy to staging environment
2. Generate test SMS links
3. Test complete user flow
4. Test on multiple devices
5. Test lockout scenarios
6. Verify PDF password protection

### **Phase 3: Production Deployment**
1. Backup current production code
2. Deploy updated `server.js`
3. Deploy updated `generate_sms_links.py`
4. Test with one real customer (pilot)
5. Monitor for issues
6. Full rollout if successful

### **Phase 4: Monitoring**
1. Monitor failed login attempts
2. Monitor lockout frequency
3. Monitor session creation
4. Monitor PDF downloads
5. Collect user feedback

---

## 📋 Rollback Plan

### **If Issues Arise:**

**Quick Rollback (5 minutes):**
1. Revert `server.js` to previous version
2. Restart server
3. Old SMS links continue to work (no password required)
4. New SMS links will need to be regenerated

**Data Compatibility:**
- Old letter JSON files (without NIC fields) will still work
- New letter JSON files (with NIC fields) are backward compatible
- No data migration required

**Rollback Command:**
```bash
# Backup current version
cp server.js server.js.backup

# Restore previous version
git checkout HEAD~1 server.js

# Restart server
npm run server
```

---

## ⚠️ Known Limitations & Considerations

### **1. NIC Data Quality**
**Issue:** If NIC is missing or incorrect in Excel file, customer cannot access letter.

**Mitigation:**
- Validate NIC data during PDF generation
- Log warnings for missing/invalid NICs
- Provide customer service fallback

### **2. Customer Support**
**Issue:** Customers may forget their NIC or enter it incorrectly.

**Mitigation:**
- Clear error messages with remaining attempts
- Customer service number prominently displayed
- Consider adding "Forgot NIC?" help link

### **3. Mobile Typing**
**Issue:** Entering long NIC on mobile keyboard can be error-prone.

**Mitigation:**
- Show NIC format example
- Auto-uppercase input
- Auto-remove spaces
- Show character count

### **4. Session Persistence**
**Issue:** Session expires when browser closes, requiring re-authentication.

**Mitigation:**
- This is intentional for security
- Clear messaging about session duration
- Fast re-authentication (NIC already known to customer)

### **5. PDF Password Complexity**
**Issue:** Some PDF readers may have issues with long alphanumeric passwords.

**Mitigation:**
- Test with multiple PDF readers
- Ensure NIC format is compatible
- Provide alternative access via HTML viewer

---

## 📞 Support & Maintenance

### **Customer Support Scenarios:**

**Scenario 1: "I forgot my National ID"**
- Response: "Your National ID is on your national identity card. If you don't have it, please call 602-3315 for assistance."

**Scenario 2: "I'm locked out"**
- Response: "For security, access is temporarily locked after multiple failed attempts. Please try again in 30 minutes or call 602-3315."

**Scenario 3: "The PDF won't open"**
- Response: "The PDF is password-protected with your National ID. Please enter your National ID when prompted to open the file."

**Scenario 4: "I entered my NIC correctly but it says invalid"**
- Response: "Please ensure you're entering your National ID without spaces. Example: A1234567890123. If the issue persists, call 602-3315."

### **Admin Monitoring:**

**Metrics to Track:**
- Failed authentication attempts per day
- Lockout frequency
- Average attempts before success
- Session duration statistics
- PDF download success rate

**Alerts to Configure:**
- High failed attempt rate (potential attack)
- Frequent lockouts (data quality issue)
- Session creation failures
- PDF download errors

---

## ✅ Approval Checklist

Before implementation, confirm:

- [ ] Security specifications reviewed and approved
- [ ] User flow approved
- [ ] SMS message format approved
- [ ] Failed attempt limit (10) approved
- [ ] Lockout duration (30 minutes) approved
- [ ] Session duration (browser close) approved
- [ ] NIC format (full, no spaces) approved
- [ ] PDF source (protected folder) approved
- [ ] File modification list reviewed
- [ ] Testing plan approved
- [ ] Deployment plan approved
- [ ] Rollback plan approved
- [ ] Customer support plan approved
 
---

  