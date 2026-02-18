# Frontend Testing Guide - SMS Links & Email Notifications

## 🎯 Overview

This guide shows you exactly how to test the new SMS Links and Email Notifications features from the web interface after deployment.

---

## 📧 Testing Email Notifications

### **Step 1: Configure Email Settings**

1. **Open your website** in browser: `https://your-domain.com`
2. **Login** to the system with your credentials
3. **Look for the new tabs** at the top - you should see 4 tabs now:
   - Generate and Combine
   - SMS Links  
   - Browse & Download
   - **Email Notifications** ← New tab

4. **Click on "Email Notifications" tab**
5. **Fill in the form**:
   - **Your Name**: Enter your name (e.g., "John Smith")
   - **Email Address**: Enter your email (e.g., "john@company.com")
6. **Click "Save Configuration"**
7. **Expected Result**: ✅ Green message "Email configuration saved successfully!"

### **Step 2: Test PDF Generation Email**

1. **Go to "Generate and Combine" tab**
2. **Upload an Excel file** (any of your existing templates)
3. **Select appropriate template** (should auto-select)
4. **Click "Generate PDFs"**
5. **Wait for processing** to complete
6. **Expected Results**:
   - ✅ PDFs generate successfully as before
   - ✅ **Check your email inbox** - you should receive an email with subject like "✅ PDF Generation Completed - output_folder_name"
   - ✅ Email should contain: folder name, PDF count, processing time, template used

### **Step 3: Test SMS Generation Email**

1. **Go to "SMS Links" tab**
2. **Select a folder** that has PDFs (from previous step or existing folder)
3. **Click "Generate SMS"** 
4. **Wait for processing** to complete
5. **Expected Results**:
   - ✅ SMS links generate successfully
   - ✅ **Check your email inbox** - you should receive an email with subject like "📱 SMS Links Generated - folder_name"
   - ✅ Email should contain: folder name, SMS count, processing time, template type

---

## 📱 Testing SMS Links Functionality

### **Step 1: Access SMS Links Tab**

1. **Click on "SMS Links" tab**
2. **Expected Result**: You should see:
   - 📁 "Folder-Based SMS Link Generation" section
   - List of available PDF folders
   - Each folder shows: PDF count, date, template, status

### **Step 2: Generate SMS Links**

1. **Look for folders** with status "Ready for SMS"
2. **Click "Generate SMS"** on a folder
3. **Expected Results**:
   - ✅ Button changes to "Generating..." with spinner
   - ✅ Processing completes (may take 1-2 minutes)
   - ✅ Success message appears: "Successfully generated X SMS links for folder_name!"
   - ✅ Button changes to "Download SMS"
   - ✅ Status changes to "SMS Ready (X links)"

### **Step 3: Download SMS File**

1. **Click "Download SMS"** button
2. **Expected Result**: 
   - ✅ CSV file downloads automatically
   - ✅ File name like: `SMS_Batch_folder_name_2024-12-21.csv`

### **Step 4: Test SMS Links**

1. **Open the downloaded CSV file** (in Excel or text editor)
2. **Copy one of the "ShortURL" links** (e.g., `https://tinyurl.com/abc123`)
3. **Open the link in a browser** (preferably mobile browser)
4. **Expected Results**:
   - ✅ Link redirects to your domain: `https://your-domain.com/letter/unique-id`
   - ✅ Letter displays properly with customer information
   - ✅ QR code is visible (if customer has complete data)
   - ✅ Letter is mobile-friendly and readable
   - ✅ "Download PDF" button works

### **Step 5: Test Multiple SMS Links**

1. **Test 3-4 different SMS links** from the CSV file
2. **Expected Results**:
   - ✅ All links work and show different customer letters
   - ✅ Each letter has correct customer information
   - ✅ QR codes display (where data is available)
   - ✅ PDF downloads work for each letter

---

## 🔍 Testing Edge Cases

### **Test 1: Folder Without Source Excel File**

1. **Look for folders** with red warning: "❌ No folder-specific Excel file found"
2. **Expected Result**: 
   - ✅ "Generate SMS" button is disabled (greyed out)
   - ✅ Clear error message explaining why SMS generation is not available

### **Test 2: Empty Folders**

1. **Expected Result**: 
   - ✅ Folders with 0 PDFs should not appear in the list
   - ✅ Only folders with actual PDFs are shown

### **Test 3: Outdated SMS Links**

1. **Generate SMS links** for a folder
2. **Regenerate PDFs** for the same folder (with different data)
3. **Go back to SMS Links tab**
4. **Expected Results**:
   - ✅ Status shows "SMS Outdated (X/Y)" where X ≠ Y
   - ✅ Orange warning icon appears
   - ✅ Button shows "Regenerate SMS" instead of "Download SMS"
   - ✅ Warning message: "SMS links are outdated - regenerate recommended"

---

## 🎨 UI/UX Testing

### **Visual Elements to Check:**

1. **Tab Navigation**:
   - ✅ 4 tabs are visible and clickable
   - ✅ Active tab is highlighted
   - ✅ Tab icons display correctly

2. **SMS Links Tab**:
   - ✅ Folder list displays in cards
   - ✅ Status icons show correctly (green checkmark, orange warning, etc.)
   - ✅ "Latest" badge appears on newest folder
   - ✅ Buttons are properly styled and responsive

3. **Email Notifications Tab**:
   - ✅ Form fields are properly aligned
   - ✅ Success/error messages display correctly
   - ✅ Configuration status shows when email is set

4. **Mobile Responsiveness**:
   - ✅ Test on mobile device or browser dev tools
   - ✅ SMS letter viewer is mobile-friendly
   - ✅ All buttons and text are readable on mobile

---

## 🚨 Troubleshooting Common Issues

### **Issue 1: New Tabs Not Showing**

**Symptoms**: Only see 2 tabs instead of 4
**Solutions**:
```bash
# Clear browser cache (Ctrl+Shift+Delete)
# Hard refresh (Ctrl+F5)
# Check if frontend was rebuilt: npm run build
# Restart application: pm2 restart app-name
```

### **Issue 2: Email Configuration Not Saving**

**Symptoms**: Error message when saving email config
**Solutions**:
- Check browser console for errors (F12)
- Verify server is running: `pm2 status`
- Check server logs: `pm2 logs app-name`

### **Issue 3: SMS Links Not Generating**

**Symptoms**: "Generate SMS" button doesn't work or shows errors
**Solutions**:
- Check if folder has source Excel file
- Verify `letter_links` directory exists and has permissions
- Check server logs for Python errors
- Test Python dependencies: `python check_email_status.py`

### **Issue 4: SMS Links Don't Open**

**Symptoms**: SMS links show 404 or redirect to homepage
**Solutions**:
- Verify domain configuration in `completion_email_service.py`
- Check if letter route is working: `/letter/test-id`
- Check Nginx configuration for letter routes

### **Issue 5: QR Codes Missing in Letter Viewer**

**Symptoms**: Letters show "QR Code Available in PDF Download" instead of actual QR
**Solutions**:
- This is expected for records with missing mobile/NIC data
- Download PDF to see if QR code is there
- Check Excel file for complete customer data

---

## ✅ Complete Testing Checklist

### **Email Notifications:**
- [ ] Email configuration tab appears
- [ ] Can save email address successfully
- [ ] Receive PDF completion email
- [ ] Receive SMS completion email
- [ ] Email templates show correct domain (not localhost)
- [ ] Email content is properly formatted

### **SMS Links:**
- [ ] SMS Links tab appears
- [ ] Can see list of PDF folders
- [ ] Can generate SMS links successfully
- [ ] Can download SMS CSV file
- [ ] SMS links work in browser
- [ ] Letter viewer displays correctly
- [ ] QR codes show (where data available)
- [ ] PDF download works from letter viewer
- [ ] Mobile-friendly letter display

### **Integration:**
- [ ] Both features work together
- [ ] Existing PDF generation still works
- [ ] No errors in browser console
- [ ] No errors in server logs
- [ ] All previous functionality intact

---

## 📊 Expected Performance

### **SMS Link Generation:**
- **Small files (1-50 records)**: 10-30 seconds
- **Medium files (51-200 records)**: 30-90 seconds  
- **Large files (200+ records)**: 1-3 minutes

### **Email Delivery:**
- **PDF completion email**: Within 30 seconds of completion
- **SMS completion email**: Within 30 seconds of completion
- **Email delivery**: 1-5 minutes (depends on email provider)

---

## 📞 Success Indicators

**✅ Everything is working correctly if:**

1. **You see 4 tabs** in the navigation
2. **Email configuration saves** without errors
3. **You receive email notifications** for both PDF and SMS generation
4. **SMS links generate** and download CSV files
5. **SMS links open** and show customer letters correctly
6. **QR codes display** in letter viewer (where data is complete)
7. **PDF downloads work** from letter viewer
8. **Mobile display** is clean and readable
9. **No console errors** in browser developer tools
10. **Server logs show** successful email sending messages

If all these work, your SMS Links and Email Notifications features are fully functional! 🎉