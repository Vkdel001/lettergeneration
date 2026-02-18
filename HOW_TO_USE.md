# PDF Generator - How to Use Guide

## Overview
This application generates personalized PDF arrears letters for insurance policyholders. It combines a React frontend with a Node.js backend that executes Python scripts to create professional PDF documents.

### 🚨 Latest Updates (November 2025)
- **PDF Sequence Ordering:** Fixed PDF combining to maintain exact Excel row order
- **Template Sequence Numbering:** All PDF templates now generate files with 001_, 002_, 003_ prefixes
- **Cross-Platform Sorting:** Fixed filesystem-dependent file ordering issues between local/VPS
- **QR Code Preservation:** Fixed corruption issues in PDF combining using PyMuPDF
- **Environment Detection:** Automatic API URL detection for local/VPS deployment
- **Password Protection:** Enhanced PyPDF2 compatibility for all versions
- **Error Handling:** Improved JavaScript error handling and user feedback

## Prerequisites

### Required Software
- **Node.js** (version 14 or higher)
- **Python** (version 3.7 or higher)
- **Web Browser** (Chrome, Firefox, Edge, Safari)

### Required Python Libraries
Install these Python packages:
```bash
# Standard packages
pip install pandas requests segno reportlab openpyxl PyPDF2

# 🚨 CRITICAL: Install PyMuPDF for QR code preservation in PDF combining
pip install PyMuPDF

# For VPS deployment (if system-managed Python environment)
pip install PyMuPDF --break-system-packages
```

### 🔧 VPS-Specific Requirements
```bash
# Create Python compatibility symlink (critical for VPS)
sudo ln -sf /usr/bin/python3 /usr/bin/python
python --version  # Should show Python 3.x
```

### Required Files
- **Excel Template**: `Generic_Template.xlsx` with required columns
- **Font Files**: Cambria fonts in `fonts/` folder
- **Logo Image**: `maucas.jpeg` for letterhead
- **Python Templates**: Various PDF generation scripts

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Verify Python Setup
Check if Python libraries are installed:
```bash
python -c "import pandas, requests, segno, reportlab; print('All libraries installed successfully')"
```

### 3. Check Required Files
Ensure these files exist:
- `fonts/cambria.ttf`
- `fonts/cambriab.ttf`
- `maucas.jpeg`
- `Generic_Template.xlsx`

## Running the Application

### Option 1: Run Both Services Together (Recommended)
```bash
npm run dev:full
```
This starts both backend and frontend simultaneously.

### Option 2: Run Services Separately

**Terminal 1 - Backend Server:**
```bash
npm run server
```
Server runs on: `http://localhost:3001`

**Terminal 2 - Frontend App:**
```bash
npm run dev
```
Frontend runs on: `http://localhost:5173`

## Using the Application

### Step 1: Access the Application
Open your web browser and go to: `http://localhost:5173`

### Step 2: Prepare Your Excel File
Your Excel file must contain these **required columns**:
- `Policy No` - Insurance policy number
- `Owner 1 Title` - Mr/Mrs/Ms
- `Owner 1 First Name` - Policyholder's first name
- `Owner 1 Surname` - Policyholder's last name
- `Owner 1 Policy Address 1` - Address line 1
- `Owner 1 Policy Address 2` - Address line 2 (optional)
- `Owner 1 Policy Address 3` - Address line 3 (optional)
- `Owner 1 Policy Address 4` - Address line 4 (optional)
- `Arrears Amount` - Outstanding amount in MUR
- `Computed Gross Premium` - Premium amount
- `No of Instalments in Arrears` - Number of missed payments
- `Frequency` - Payment frequency (Monthly/Quarterly/etc.)
- `EMAIL_ID` - Email address for sending PDFs
- `Agent No` - Agent number (optional)

### Step 3: Upload Excel File
1. Click **"Choose File"** button
2. Select your Excel file
3. Wait for file validation and preview

### Step 4: Select PDF Template
Choose from available templates:
- **SPH_PDF_CREATION_4JunOk_Alignment.py** - Standard SPH template with alignment
- **SPH_PDF_CREATION_4JunOk.py** - Basic SPH template
- **COMPANY_PDF_CREATION_4JunOk.py** - Company template
- **JPH_PDF_CREATION_4JunOk.py** - JPH template

### Step 5: Configure Options
- **Auto Download**: Automatically download generated PDFs
- **Send Emails**: Email PDFs to policyholders (requires EmailJS setup)
- **Batch Size**: Number of PDFs to process at once
- **Concurrent Limit**: Parallel processing limit

### Step 6: Generate PDFs
1. Click **"Generate PDFs"** button
2. Monitor progress bar
3. View results and download files

## Features

### PDF Content
Each generated PDF includes:
- **Letterhead** with company logo
- **Date** in DD-Mon-YYYY format (e.g., 09-Sep-2025)
- **Policyholder address**
- **Arrears details table** with comma-formatted currency (e.g., 5,000.00)
- **Payment instructions** (in bold)
- **QR code** for mobile payments
- **Professional footer**

### PDF Sequence Ordering (New Feature)
- **Individual PDFs** are generated with sequence numbers: `001_Policy123_John_Doe.pdf`
- **Combined PDFs** maintain exact Excel row order (Row 1 → Page 1, Row 2 → Page 2, etc.)
- **Cross-platform compatibility** ensures consistent ordering on all systems
- **Zero-padded numbering** (001, 002, 010, 100) for proper alphabetical sorting

### Currency Formatting
- Amounts display with commas: `MUR 5,000.00`
- Consistent formatting across all templates

### QR Code Payments
- Integrated with Zwenn Pay system
- Works with Juice and MyT Money apps
- Automatic generation for each policy

## Email Configuration (Optional)

To send PDFs via email, configure EmailJS:

1. **Get EmailJS Account**: Sign up at emailjs.com
2. **Configure Settings**: Click gear icon in app
3. **Enter Credentials**:
   - Service ID
   - Template ID
   - Public Key

## Troubleshooting

### 🚨 Critical Issues (Fixed in Latest Version)

**QR Codes Missing in Combined PDFs**
- ✅ **FIXED**: Now uses PyMuPDF for better image preservation
- Ensure PyMuPDF is installed: `pip install PyMuPDF`
- Test: Generate and combine PDFs, verify QR codes are intact

**"Failed to start Python process" (VPS)**
- ✅ **FIXED**: Python compatibility symlink created
- Check: `python --version` should show Python 3.x
- Fix: `sudo ln -sf /usr/bin/python3 /usr/bin/python`

**"Connection Refused" Errors (VPS)**
- ✅ **FIXED**: Environment-aware API URLs
- Frontend automatically detects local vs VPS environment
- No manual URL changes needed

**JavaScript Errors (normalize, emailData)**
- ✅ **FIXED**: Added compatibility fallbacks
- Clear browser cache and hard refresh (Ctrl+F5)
- Check browser console for remaining errors

**Password Protection Not Working**
- ✅ **FIXED**: PyPDF2 version compatibility added
- Works with both old and new PyPDF2 versions
- Test: Check if protected folder has password-protected PDFs

### Common Issues

**"Excel file validation failed"**
- Check required columns are present
- Ensure data types are correct
- Verify file is not corrupted

**"Python script execution failed"**
- Check Python libraries are installed
- Verify font files exist in `fonts/` folder
- Ensure `maucas.jpeg` logo file exists
- **NEW**: Check Python symlink: `which python`

**"EBUSY: resource busy or locked"**
- Close any open PDF files
- Close Windows Explorer in output folder
- Restart the server

**"Combined PDFs in wrong order"**
- ✅ **FIXED in v1.2**: All templates now use sequence numbering
- Check if PDFs have 001_, 002_ prefixes: `ls output_*/unprotected/ | head -5`
- Clear old non-sequenced PDFs: `find output_*/ -name "*.pdf" ! -name "[0-9][0-9][0-9]_*"`
- Regenerate PDFs if mixing old and new files

**"Failed to fetch templates"**
- Ensure backend server is running on port 3001
- Check for firewall/antivirus blocking
- Verify CORS settings
- **NEW**: Check if API URLs are correct in browser network tab

### 🔍 Diagnostic Commands

**Check Python Environment:**
```bash
python --version          # Should show Python 3.x
which python             # Should point to /usr/bin/python
python3 -c "import fitz; print('PyMuPDF OK')"  # Should not error
```

**Test PDF Generation:**
```bash
python3 JPH_Fresh.py --help                    # Should show help
python3 combine_pdfs.py --help                 # Should show help
```

**Verify Sequence Ordering:**
```bash
# Check if PDFs have sequence numbers
ls output_*/unprotected/ | head -5              # Should show 001_, 002_, 003_
# Test combining maintains order
python3 combine_pdfs.py --folder output_test_folder --output test_combined.pdf
```

**Check Services:**
```bash
# Local development
curl -I http://localhost:3001/api/status       # Should return 200 OK
curl -I http://localhost:5173                  # Should return 200 OK

# VPS deployment
curl -I http://your-vps-ip:3001/api/status     # Should return 200 OK
curl -I http://your-vps-ip:8080                # Should return 200 OK
```

### File Locations
- **Generated PDFs**: `generated_pdfs/` folder
- **Temporary uploads**: `temp_uploads/` folder
- **Output letters**: `output_letters/` folder (for direct Python execution)

## Template Differences

### Font Styles
- **SPH Alignment Template**: Cambria 11pt (readable)
- **Other Templates**: Helvetica 8pt (compact)

### Layout Features
- **Alignment Template**: Enhanced formatting and spacing
- **Standard Templates**: Basic layout with smaller fonts

## Performance Tips

1. **Batch Processing**: Use smaller batch sizes (10-20) for better performance
2. **Concurrent Limit**: Keep at 3-5 for optimal speed
3. **File Management**: Clear output folders regularly
4. **Memory**: Close unnecessary applications when processing large files

## Support

For technical issues:
1. Check console logs in browser (F12)
2. Review server logs in terminal
3. Verify all dependencies are installed
4. Ensure all required files are present

## File Structure
```
project/
├── src/                    # React frontend
├── fonts/                  # Cambria font files
├── generated_pdfs/         # Output PDFs
├── temp_uploads/           # Temporary file storage
├── server.js              # Backend server
├── pdf_generator_wrapper.py # Python script wrapper
├── Generic_Template.xlsx   # Excel template
├── maucas.jpeg            # Company logo
└── *.py                   # PDF generation templates
```

---

## 🔧 Version History

### Version 1.2 (November 2025) - Sequence Ordering
- **PDF Sequence Ordering**: All templates generate PDFs with 001_, 002_, 003_ prefixes
- **Excel Row Order Preservation**: Combined PDFs maintain exact Excel row sequence
- **Cross-Platform File Sorting**: Fixed random ordering issues on different filesystems
- **Template Updates**: Updated all 6 PDF generation templates (JPH, SPH, Company, MED variants)

### Version 1.1 (October 2025) - Critical Fixes
- **QR Code Preservation**: Fixed corruption in PDF combining using PyMuPDF
- **Python Compatibility**: Fixed `python` vs `python3` command issues
- **Environment Detection**: Automatic API URL detection for local/VPS
- **Password Protection**: Enhanced PyPDF2 compatibility for all versions
- **Error Handling**: Improved JavaScript error handling and user feedback
- **Memory Management**: Better handling of large PDF files

### Version 1.0 (September 2025) - Initial Release
- Basic PDF generation functionality
- Excel file processing
- Email integration
- Multiple template support

---

**Last Updated**: November 2025
**Version**: 1.2 (Sequence Ordering Applied)

**⚠️ IMPORTANT**: 
- **v1.2 Users**: All PDF templates now generate sequenced files (001_, 002_, etc.) for proper ordering
- **v1.1 Users**: Ensure PyMuPDF is installed and Python symlink is created to prevent QR code corruption
- **Legacy Users**: Clear old PDF folders to avoid mixing sequenced and non-sequenced files


---

## 📱 SMS Link Feature (NEW - December 2025)

### Overview
The SMS Link feature is an **additional functionality** that generates unique web links for each customer's arrears letter and creates SMS bulk files for third-party SMS sending. This feature works alongside existing PDF generation without disrupting current workflows.

### Key Benefits
- ✅ **Instant Delivery**: SMS reaches customers immediately (98% open rate vs 20% email)
- ✅ **Cost Reduction**: No printing, postage, or email delivery costs
- ✅ **Mobile Friendly**: Optimized letter viewer for smartphones
- ✅ **Better Tracking**: Know who viewed their letter and when
- ✅ **Secure Links**: 30-day expiry and access limits for security

### How to Use SMS Links

#### Step 1: Generate PDFs First
1. Upload Excel file and generate PDFs as usual
2. Wait for PDF generation to complete
3. SMS Link section appears automatically

#### Step 2: Generate SMS Links
1. Click **"Generate SMS Links"** button in the SMS Link section
2. System processes each customer record:
   - Creates unique secure URL for each letter
   - Generates shortened URL via TinyURL
   - Saves letter data as JSON
   - Creates SMS message text
3. Wait for "Ready" status (usually 1-2 minutes for 1000 records)

#### Step 3: Download SMS File
1. Click **"Download SMS File"** button
2. CSV file downloads automatically
3. File format: `SMS_Batch_[Folder]_[Date].csv`

#### Step 4: Send SMS (External)
1. Import CSV into your SMS service provider
2. Send bulk SMS to customers
3. Customers receive SMS with short links

#### Step 5: Customer Experience
1. Customer clicks SMS link on mobile phone
2. Opens mobile-friendly letter viewer in browser
3. Can view letter, download PDF, or print
4. Link expires after 30 days

### SMS File Format

The generated CSV file contains:

```csv
Mobile,Message,ShortURL,Policy,CustomerName,Status
57123456,"Dear Mr Doe, your NICL arrears notice: https://tinyurl.com/abc123",https://tinyurl.com/abc123,00407/0094507,Mr John Doe,Ready
57789012,"Dear Mrs Smith, your NICL arrears notice: https://tinyurl.com/def456",https://tinyurl.com/def456,00407/0094508,Mrs Jane Smith,Ready
```

**Columns:**
- **Mobile**: Customer mobile number (from MOBILE_NO column)
- **Message**: Complete SMS text with personalized greeting and link
- **ShortURL**: Shortened URL for SMS (via TinyURL)
- **Policy**: Policy number for reference
- **CustomerName**: Customer name for verification
- **Status**: Always "Ready" (for SMS provider compatibility)

### Letter Viewer Features

When customers click the SMS link, they see:

- **Professional NICL branding** with logo and colors
- **Complete arrears notice** with all policy details
- **Policy information table** showing premium and arrears
- **Download PDF button** to save letter locally
- **Print button** for physical copy
- **Expiry notice** showing link validity period
- **Contact information** for customer support

### Security Features

#### Link Security
- **Unique IDs**: Non-guessable 16-character identifiers
- **Expiration**: 30-day automatic expiry
- **Access Limits**: Maximum 10 views per link
- **HTTPS Only**: Secure transmission required
- **No Indexing**: Search engines blocked

#### Data Protection
- **Temporary Storage**: Letter data stored as JSON files
- **Access Logging**: Track who viewed what and when
- **Automatic Cleanup**: Expired letters can be purged
- **No Personal Data in URLs**: Only unique IDs exposed

### File Structure

SMS Link data is stored in:

```
letter_links/
├── output_sph_November2025/
│   ├── abc123def456.json     # Letter 1 data
│   ├── xyz789ghi012.json     # Letter 2 data
│   └── sms_batch.csv         # SMS bulk file
└── output_jph_November2025/
    ├── def456abc123.json
    └── sms_batch.csv
```

### Cost Analysis

#### SMS Costs (Estimated)
- **Bulk SMS**: ~MUR 0.50 - 1.00 per SMS
- **1,500 customers**: ~MUR 750 - 1,500 per batch
- **Monthly savings**: Eliminate printing/postage costs

#### Infrastructure Costs
- **Storage**: Minimal (JSON files, ~2KB each)
- **Bandwidth**: Low (HTML pages, ~50KB each)
- **URL Shortening**: Free (TinyURL)

### Troubleshooting SMS Links

**"Output folder not found"**
- Generate PDFs first before creating SMS links
- SMS links require existing PDF files to reference

**"No mobile numbers found"**
- Check Excel file has MOBILE_NO column
- Verify mobile numbers are not empty or "NaN"
- Ensure mobile numbers are in correct format

**"URL shortening failed"**
- Check internet connection
- TinyURL API may be temporarily unavailable
- System will use long URLs as fallback

**"Letter not found" (Customer)**
- Link may have expired (30 days)
- Link may have been accessed too many times (10 views)
- Check if letter data JSON file exists

**"SMS file download failed"**
- Ensure SMS links were generated successfully
- Check browser download settings
- Try refreshing the page and downloading again

### Testing SMS Links

To test the SMS link feature:

```bash
# Run the test script
python test_sms_generation.py

# Expected output:
# [TEST] ✅ SUCCESS: SMS link generation test passed!
# [TEST] Links generated: 2
# [TEST] JSON files created: 2
# [TEST] CSV files created: 1
```

### API Endpoints (For Developers)

**Generate SMS Links:**
```
POST /api/generate-sms-links
Body: { outputFolder: "output_sph_November2025", template: "SPH_Fresh.py" }
Response: { success: true, linksGenerated: 1500, smsFileReady: true }
```

**Download SMS File:**
```
GET /api/download-sms-file/:outputFolder
Response: CSV file download
```

**View Letter (Customer):**
```
GET /letter/:uniqueId
Response: HTML letter viewer page
```

**Download PDF (Customer):**
```
GET /api/download-pdf/:uniqueId
Response: PDF file download
```

### Integration with Existing Workflows

The SMS Link feature integrates seamlessly:

1. **Existing PDF Generation**: ✅ Unchanged, works as before
2. **New SMS Option**: ✅ Additional step after PDF generation
3. **Combine PDFs**: ✅ Still works for unprotected PDFs
4. **Email Functionality**: ✅ Unchanged, can use both SMS and email
5. **File Browser**: ✅ Still works for downloading individual PDFs

**No disruption to existing processes - purely additive functionality.**

### Best Practices

1. **Always generate PDFs first** before creating SMS links
2. **Test with small batch** (10-20 records) before full deployment
3. **Verify mobile numbers** in Excel file before processing
4. **Keep SMS messages short** (under 160 characters when possible)
5. **Monitor link usage** to understand customer engagement
6. **Clean up expired links** periodically to save storage space

### Future Enhancements (Planned)

- 📧 Email notifications when links are accessed
- 📊 Analytics dashboard for link usage
- 🔄 Automatic link renewal for active customers
- 📱 SMS delivery integration (direct sending)
- 🎨 Customizable letter viewer themes

---

**SMS Link Feature Status**: ✅ **IMPLEMENTED AND TESTED**  
**Version**: 1.3 (December 2025)  
**Test Results**: All tests passed successfully  
**Production Ready**: Yes
