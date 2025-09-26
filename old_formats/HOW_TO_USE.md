# PDF Generator - How to Use Guide

## Overview
This application generates personalized PDF arrears letters for insurance policyholders. It combines a React frontend with a Node.js backend that executes Python scripts to create professional PDF documents.

## Prerequisites

### Required Software
- **Node.js** (version 14 or higher)
- **Python** (version 3.7 or higher)
- **Web Browser** (Chrome, Firefox, Edge, Safari)

### Required Python Libraries
Install these Python packages:
```bash
pip install pandas requests segno reportlab openpyxl
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

### Common Issues

**"Excel file validation failed"**
- Check required columns are present
- Ensure data types are correct
- Verify file is not corrupted

**"Python script execution failed"**
- Check Python libraries are installed
- Verify font files exist in `fonts/` folder
- Ensure `maucas.jpeg` logo file exists

**"EBUSY: resource busy or locked"**
- Close any open PDF files
- Close Windows Explorer in output folder
- Restart the server

**"Failed to fetch templates"**
- Ensure backend server is running on port 3001
- Check for firewall/antivirus blocking
- Verify CORS settings

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

**Last Updated**: September 2025
**Version**: 1.0