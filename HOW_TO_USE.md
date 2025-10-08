# PDF Generator - How to Use Guide

## Overview
This application generates personalized PDF arrears letters for insurance policyholders. It combines a React frontend with a Node.js backend that executes Python scripts to create professional PDF documents.

### 🚨 Latest Updates (October 2025)
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

**Last Updated**: October 2025
**Version**: 1.1 (Critical Fixes Applied)

**⚠️ IMPORTANT**: If upgrading from v1.0, ensure PyMuPDF is installed and Python symlink is created to prevent QR code corruption and compatibility issues.