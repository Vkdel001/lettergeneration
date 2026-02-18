# Excel File Copy Fix - Deployment Guide

## ✅ **Changes Made**

**File Modified**: `pdf_generator_wrapper.py`

### **Change Summary**:
- **Moved Excel file copy code earlier** in the process (before file is marked as processed)
- **Removed duplicate code** that ran too late
- **Added better logging** to show file size and confirm copy

## 🔧 **What Was Fixed**

### **Before (Problem)**:
1. PDF generation completes ✅
2. File renamed to `_processed.xlsx` ✅
3. Excel copy code runs → looks for original filename ❌ (doesn't exist)
4. SMS generation fails → no Excel file in output folder ❌

### **After (Fixed)**:
1. PDF generation completes ✅
2. **Excel file copied to output folder** ✅ (NEW - runs first!)
3. File renamed to `_processed.xlsx` ✅
4. SMS generation works → Excel file available ✅

## 📋 **Deployment Steps**

### **Step 1: Commit Changes Locally**
```bash
# Check what changed
git diff pdf_generator_wrapper.py

# Add and commit
git add pdf_generator_wrapper.py
git commit -m "Fix Excel file copy timing for SMS generation

- Move Excel copy before file is marked as processed
- Remove duplicate Excel copy code that ran too late
- Add file size logging for verification
- Fixes issue where SMS generation couldn't find Excel file"

# Push to GitHub
git push origin main
```

### **Step 2: Deploy to VPS**
```bash
# SSH into VPS
ssh root@your-vps-ip

# Navigate to project
cd /var/www/pdf-generator

# Pull latest changes
git pull origin main

# Verify the change
grep -n "Save Excel file copy BEFORE" pdf_generator_wrapper.py

# Should show the new code around line 178
```

### **Step 3: No Restart Needed**
```
✅ Python scripts are read fresh each time
✅ Changes take effect immediately on next PDF generation
❌ No PM2 restart required
```

## ✅ **Verification After Deployment**

### **Test 1: Generate PDFs**
1. Go to your website
2. Upload Excel file
3. Generate PDFs (any template)
4. Check PM2 logs:

```bash
# On VPS
pm2 logs --lines 50 | grep "SMS-PREP"

# Should see:
# [SMS-PREP] Saved Excel file copy for SMS generation: output_xxx/output_xxx_source.xlsx
# [SMS-PREP] File size: 670,758 bytes
```

### **Test 2: Check Output Folder**
```bash
# On VPS
ls -la output_sph_January2026/*.xlsx

# Should show:
# output_sph_January2026_source.xlsx
```

### **Test 3: Generate SMS Links**
1. Go to SMS Links tab
2. Select the folder
3. Click "Generate SMS"
4. Should work without errors ✅

## 📊 **Expected Log Output**

After the fix, you should see this in PM2 logs during PDF generation:

```
Template executed successfully
[SMS-PREP] Saved Excel file copy for SMS generation: output_sph_January2026/output_sph_January2026_source.xlsx
[SMS-PREP] File size: 670,758 bytes
Marked file as processed: Generic_Template_processed.xlsx
Found 5234 PDFs in protected folder
Found 5234 PDFs in unprotected folder
Successfully generated 5234 PDF files in output_sph_January2026
```

## 🎯 **Benefits**

- ✅ **Reliable SMS generation**: Excel file always available in output folder
- ✅ **No manual copying**: Automatic during PDF generation
- ✅ **Better logging**: Shows file size for verification
- ✅ **Cleaner code**: Removed duplicate logic
- ✅ **Correct timing**: Runs before file is renamed

## 🚨 **Rollback Plan** (If Needed)

If something goes wrong:

```bash
# On VPS
cd /var/www/pdf-generator

# Revert to previous version
git log --oneline -5
git reset --hard <previous-commit-hash>

# Or manually copy Excel file
cp Generic_Template_processed.xlsx output_xxx/output_xxx_source.xlsx
```

## 📞 **Support**

If Excel file still doesn't get copied:

1. **Check logs**: `pm2 logs --lines 100 | grep "SMS-PREP"`
2. **Check file exists**: `ls -la Generic_Template*.xlsx`
3. **Check output folder**: `ls -la output_xxx/*.xlsx`
4. **Manual copy**: `cp Generic_Template_processed.xlsx output_xxx/output_xxx_source.xlsx`

---

**Status**: ✅ Changes applied and ready for deployment  
**Risk Level**: Low - only changes timing of existing functionality  
**Downtime**: None - no restart required  
**Testing**: Verify with next PDF generation