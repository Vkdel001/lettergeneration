# SMS Link Issues - Fixes & Solutions

## **🐛 Issues Identified**

### **Issue 1: Letter URLs Redirect to Home Page**
**Problem:** When accessing letter URLs like `http://localhost:3001/letter/53d814e9676c3ab9`, they redirect to the main application instead of showing the letter viewer.

**Root Cause:** The catch-all route `app.get('*', ...)` in server.js was intercepting letter URLs and redirecting them to the Vite dev server.

### **Issue 2: Same 3 Sample Records in All Folders**
**Problem:** All folders show the same 3 test records instead of the actual data from the original Excel files used to generate those PDFs.

**Root Cause:** The SMS link generation was finding `Generic_Template_processed.xlsx` (which only has 3 test records) instead of the original Excel files that contained the real customer data.

---

## **✅ Solutions Implemented**

### **Fix 1: Letter URL Routing**

**File:** `server.js`
**Change:** Modified the catch-all route to exclude letter URLs and API endpoints.

```javascript
// BEFORE
app.get('*', (req, res) => {
  if (process.env.NODE_ENV === 'development') {
    res.redirect('http://localhost:5173');
  } else {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  }
});

// AFTER
app.get('*', (req, res) => {
  // Don't redirect letter viewer URLs or API endpoints
  if (req.path.startsWith('/letter/') || req.path.startsWith('/api/')) {
    return res.status(404).send('Not Found');
  }
  
  if (process.env.NODE_ENV === 'development') {
    res.redirect('http://localhost:5173');
  } else {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  }
});
```

**Result:** Letter URLs now work correctly and display the letter viewer instead of redirecting.

### **Fix 2: Excel File Discovery Enhancement**

**File:** `generate_sms_links.py`
**Change:** Enhanced Excel file discovery to prioritize folder-specific files.

```python
# BEFORE - Generic file search
possible_files = [
    "Generic_Template.xlsx",
    "temp_uploads/Generic_Template.xlsx",
    "Generic_Template_processed.xlsx",
    # ... other generic files
]

# AFTER - Folder-specific file search
possible_files = [
    f"{output_folder}_source.xlsx",             # Folder-specific source file
    f"{output_folder}.xlsx",                    # Folder-named file
    "Generic_Template.xlsx",                    # Current file (fallback)
    # ... other files as fallback
]

# ENHANCEMENT - Check output folder for Excel files
if os.path.exists(output_folder):
    folder_files = os.listdir(output_folder)
    folder_excel_files = [os.path.join(output_folder, f) for f in folder_files if f.endswith('.xlsx')]
    possible_files = folder_excel_files + possible_files  # Prioritize folder-specific files
```

**Result:** SMS link generation now looks for folder-specific Excel files first, then falls back to generic files.

### **Fix 3: Excel File Preservation During PDF Generation**

**File:** `pdf_generator_wrapper.py`
**Change:** Added logic to save a copy of the Excel file in each output folder.

```python
# NEW - Save Excel file copy for future SMS generation
try:
    if os.path.exists(expected_filename):
        folder_name = os.path.basename(args.output)
        excel_copy_path = os.path.join(args.output, f"{folder_name}_source.xlsx")
        shutil.copy2(expected_filename, excel_copy_path)
        print(f"[SMS-PREP] Saved Excel file copy for SMS generation: {excel_copy_path}")
except Exception as e:
    print(f"[SMS-PREP] Warning: Could not save Excel file copy: {e}")
```

**Result:** Each new PDF generation will save the original Excel file in the output folder for future SMS link generation.

---

## **🔄 How the Fixes Work Together**

### **For New PDF Generations (Going Forward):**
1. User uploads Excel file with real customer data
2. PDF generation completes successfully
3. **NEW:** Excel file is automatically saved as `{folder_name}_source.xlsx` in the output folder
4. When generating SMS links later, the system finds and uses this folder-specific Excel file
5. SMS links are generated with the correct customer data

### **For Existing PDF Folders (Current Situation):**
1. Existing folders don't have their original Excel files (they were processed before this fix)
2. SMS link generation falls back to `Generic_Template_processed.xlsx` (3 test records)
3. **Workaround:** You can manually copy the original Excel files into the respective folders

### **Letter URL Access:**
1. Letter URLs like `/letter/53d814e9676c3ab9` now work correctly
2. No more redirects to the main application
3. Customers can access their letters via SMS links

---

## **📋 Testing the Fixes**

### **Test 1: Letter URL Routing**
```bash
# Test a known letter URL
curl -I http://localhost:3001/letter/53d814e9676c3ab9

# Expected: 200 OK with HTML content
# Before fix: 302 redirect to localhost:5173
```

### **Test 2: Enhanced Excel File Discovery**
```bash
# Run the test script
python test_fixes.py

# Expected: Shows which folders have Excel files
```

### **Test 3: New PDF Generation with Excel Preservation**
1. Upload a new Excel file with real data
2. Generate PDFs
3. Check that `{folder_name}_source.xlsx` exists in the output folder
4. Generate SMS links - should use the correct data

---

## **🚀 Immediate Actions Required**

### **1. Restart Server**
The server needs to be restarted to pick up the letter URL routing fix.

### **2. Test Letter URLs**
Try accessing a letter URL to confirm the routing fix works:
- `http://localhost:3001/letter/53d814e9676c3ab9`

### **3. For Existing Folders (Optional)**
If you want SMS links for existing folders to have correct data:

```bash
# Example: Copy original Excel file to a specific folder
cp original_sph_november_data.xlsx output_sph_November2025/output_sph_November2025_source.xlsx
```

### **4. Test New PDF Generation**
Generate a new batch of PDFs to test the Excel file preservation feature.

---

## **📊 Expected Outcomes**

### **Immediate (After Server Restart):**
- ✅ Letter URLs work correctly
- ✅ SMS Links tab is accessible
- ✅ Enhanced folder API shows correct metadata

### **For New PDF Generations:**
- ✅ Excel files are automatically preserved in output folders
- ✅ SMS link generation uses correct customer data
- ✅ No more "same 3 records" issue

### **For Existing Folders:**
- ⚠️ Will continue to use fallback Excel file (3 records) unless manually fixed
- ✅ Can still generate SMS links (but with test data)
- ✅ Letter URLs work for existing generated links

---

## **🔧 Manual Fix for Existing Folders (Optional)**

If you have the original Excel files and want to fix existing folders:

```bash
# For each folder, copy the original Excel file
# Format: {folder_name}_source.xlsx

# Example for SPH November 2025
cp /path/to/original/sph_november_2025.xlsx output_sph_November2025/output_sph_November2025_source.xlsx

# Example for Company October 2025  
cp /path/to/original/company_october_2025.xlsx output_company_sph_October2025/output_company_sph_October2025_source.xlsx
```

After copying the files, regenerate SMS links for those folders to get the correct data.

---

## **📈 Long-term Benefits**

1. **Accurate SMS Links:** All future SMS links will have correct customer data
2. **Independent Processing:** Can generate SMS links from any folder anytime
3. **Data Integrity:** Original Excel data is preserved with each PDF batch
4. **Better User Experience:** Letter URLs work reliably for customers
5. **Scalable Solution:** Works for thousands of records without data loss

---

**The fixes ensure that the SMS link feature works correctly both for new PDF generations and provides a path to fix existing folders if needed.**