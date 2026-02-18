# Quick Test Guide - NIC Password Protection

## 🚀 Quick Start Testing

### **Step 1: Generate Test SMS Links**

```bash
# Option 1: Use existing PDF folder
python generate_sms_links.py --folder output_sph_December2025 --template SPH_Fresh.py --base-url http://localhost:3001

# Option 2: Generate new PDFs first, then SMS links
# (Upload Excel file through UI, generate PDFs, then generate SMS links)
```

### **Step 2: Find a Test Link**

```bash
# Open the SMS batch file
notepad letter_links\output_sph_December2025\sms_batch.csv

# Copy a ShortURL or use the long URL format:
# http://localhost:3001/letter/{uniqueId}
```

### **Step 3: Test Password Entry**

1. Open the link in browser
2. Should see: "Dear Valued Customer" (NO customer data)
3. Enter NIC from Excel file (no spaces)
4. Click "Access Document"
5. Should see full letter with customer data

### **Step 4: Test PDF Download**

1. After successful login
2. Click "📥 Download PDF" button
3. PDF downloads
4. Open PDF → Enter NIC as password
5. PDF should open

---

## 🧪 Test Scenarios

### **✅ Happy Path**
```
1. Click link → Password page
2. Enter correct NIC → Letter displays
3. Download PDF → PDF requires NIC password
4. Close browser → Session ends
5. Reopen link → Password required again
```

### **❌ Failed Login**
```
1. Click link → Password page
2. Enter wrong NIC → "Invalid National ID. 9 attempts remaining"
3. Try again (wrong) → "8 attempts remaining"
4. Continue until 0 attempts → "Too many failed attempts. Try again in 30 minutes"
```

### **🔒 Lockout Recovery**
```
1. Get locked out (10 failed attempts)
2. Wait 30 minutes
3. Try again → Should work
```

---

## 📋 What to Check

### **Password Page:**
- [ ] Shows NICL logo
- [ ] Says "Dear Valued Customer"
- [ ] NO policy number visible
- [ ] NO customer name visible
- [ ] Has NIC input field
- [ ] Shows example format
- [ ] Has help contact (602-3315)

### **After Successful Login:**
- [ ] Shows full letter content
- [ ] Shows customer name
- [ ] Shows policy details
- [ ] Shows QR code
- [ ] Has download button
- [ ] Has print button

### **PDF Download:**
- [ ] PDF downloads successfully
- [ ] PDF requires password to open
- [ ] Password is customer's NIC
- [ ] PDF contains QR code

---

## 🔍 Where to Find Test Data

### **NIC Values:**
Look in your Excel file (`Generic_Template.xlsx`):
- Column: `NIC`
- Example: `A1234567890123`

### **Letter URLs:**
After generating SMS links, check:
- File: `letter_links/{folder}/sms_batch.csv`
- Column: `ShortURL` or construct: `http://localhost:3001/letter/{uniqueId}`

### **Unique IDs:**
Check JSON files in:
- Folder: `letter_links/{folder}/`
- Files: `{uniqueId}.json`

---

## ⚡ Quick Commands

### **Restart Server:**
```bash
# Stop current server (Ctrl+C in terminal)
# Start again
npm run server
```

### **Check Server Logs:**
```bash
# Look for these messages:
[AUTH] Session created for letter...
[AUTH] Successful authentication for letter...
[AUTH] Failed authentication for letter...
```

### **View Letter JSON:**
```bash
# Open a letter JSON file
notepad letter_links\output_sph_December2025\{uniqueId}.json

# Check for:
# - nicHash field
# - accessAttempts array
# - lockedUntil field
```

---

## 🐛 Common Issues & Fixes

### **Issue: "Invalid National ID" but NIC is correct**
**Fix:** 
- Remove all spaces from NIC
- Try uppercase version
- Check NIC in Excel file matches

### **Issue: Password page shows customer data**
**Fix:** This shouldn't happen! Check server.js implementation

### **Issue: PDF won't open**
**Fix:**
- Ensure using protected folder PDF
- Password is full NIC (no spaces)
- Try uppercase NIC

### **Issue: Session not persisting**
**Fix:**
- Check browser cookies are enabled
- Cookie name: `nicl_letter_session`
- Clear cookies and try again

---

## 📞 Need Help?

**Check:**
1. Server is running: http://localhost:3001
2. Server logs for errors
3. Browser console for JavaScript errors
4. Letter JSON files are created correctly

**Contact:** 602-3315

---

**Happy Testing! 🎉**
