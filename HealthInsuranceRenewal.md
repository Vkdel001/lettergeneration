# Healthcare Insurance Renewal System

## Overview
This system automates the generation, merging, and processing of healthcare insurance renewal letters. It consists of three main Python scripts that work together to create professional renewal documents with QR codes for payment processing.

## System Components

### 1. healthcare_renewal_final.py
**Purpose:** Generates individual healthcare renewal letters with QR codes for payment

**Key Features:**
- Reads customer data from Excel file
- Generates personalized PDF renewal letters
- Creates QR codes for payment via ZwennPay API
- Includes multiple logos and branding elements
- Handles multi-page documents with proper formatting

**Output:** Individual PDF files in `output_renewals/` folder

### 2. simple_merge.py
**Purpose:** Merges individual renewal letters with required forms to create complete renewal packages

**Key Features:**
- Combines renewal letters with acceptance forms and policy documents
- Uses PyMuPDF for reliable PDF handling
- Creates backup files before processing
- Provides detailed progress reporting
- Handles errors gracefully

**Output:** Enhanced individual PDFs with all required forms attached

### 3. health_renewal_mergefile.py
**Purpose:** Combines all individual renewal letters into a single PDF for batch printing

**Key Features:**
- Merges all renewal letters from `output_renewals/` folder
- Creates timestamped output files
- Sorts files alphabetically for consistent ordering
- Provides processing statistics
- Optimized for printing workflows

**Output:** Single merged PDF file for printing

## Required Files

### Excel Data Files
| File Name | Purpose | Required Columns |
|-----------|---------|------------------|
| `RENEWAL_LISTING.xlsx` | Main customer data | POL_NO, NAME, SURNAME, TITLE, ADDRESS1-3, EXPIRY_POL_FROM_DT, EXPIRY_POL_TO_DT, REN_POL_START_DT, REN_POL_TO_DT, PLAN, CAT_PLAN, INPATIENT_LIMIT, OUTPATIENT_LIMIT, CAT_LIMIT, TOTAL_PREMIUM, FSC_LEVY, MOB_NO |

### PDF Form Files (for simple_merge.py)
| File Name | Purpose |
|-----------|---------|
| `Renewal Acceptance Form - HealthSense Plan V2 0.pdf` | Customer acceptance form |
| `HEALTHSENSE _SOB - FEB 2025.pdf` | Statement of Benefits document |
| `HEALTHSENSE CAT COVER_SOB - FEB 2025.pdf` | Catastrophe cover benefits |

### Logo and Image Files
| File Name | Purpose | Dimensions |
|-----------|---------|------------|
| `NICLOGO.jpg` | Main NIC company logo | 120px width (auto height) |
| `isphere_logo.jpg` | NIC I.sphere app promotion | 220px width (auto height) |
| `maucas2.jpeg` | Payment system logo | 110px width (auto height) |
| `zwennPay.jpg` | ZwennPay payment logo | 80px width (auto height) |

### Font Files
| File Name | Purpose |
|-----------|---------|
| `fonts/cambria.ttf` | Regular text font |
| `fonts/cambriab.ttf` | Bold text font |

## Workflow Process

### Step 1: Generate Individual Renewal Letters
```bash
python healthcare_renewal_final.py
```
**Prerequisites:**
- `RENEWAL_LISTING.xlsx` with customer data
- All logo files in place
- Font files in `fonts/` folder
- Internet connection for QR code generation

**Output:**
- Individual PDF files in `output_renewals/` folder
- QR code PNG files for each policy
- Console progress reporting

### Step 2: Merge with Forms (Optional)
```bash
python simple_merge.py
```
**Prerequisites:**
- Completed Step 1
- All required PDF form files
- PyMuPDF installed (`pip install PyMuPDF`)

**Output:**
- Enhanced PDFs with forms attached
- Backup files created automatically
- Progress and statistics reporting

### Step 3: Create Print-Ready Merged File
```bash
python health_renewal_mergefile.py
```
**Prerequisites:**
- Completed Step 1 (and optionally Step 2)
- PyMuPDF installed

**Output:**
- Single timestamped PDF: `Healthcare_Renewal_Letters_Merged_YYYYMMDD_HHMMSS.pdf`
- Ready for batch printing

## Technical Requirements

### Python Dependencies
```bash
pip install pandas openpyxl requests segno reportlab PyPDF2 PyMuPDF pillow
```

### System Requirements
- Python 3.7 or higher
- Windows/Linux/macOS compatible
- Internet connection for QR code generation
- Sufficient disk space for PDF generation

## File Structure
```
project_root/
├── healthcare_renewal_final.py
├── simple_merge.py
├── health_renewal_mergefile.py
├── RENEWAL_LISTING.xlsx
├── fonts/
│   ├── cambria.ttf
│   └── cambriab.ttf
├── NICLOGO.jpg
├── isphere_logo.jpg
├── maucas2.jpeg
├── zwennPay.jpg
├── Renewal Acceptance Form - HealthSense Plan V2 0.pdf
├── HEALTHSENSE _SOB - FEB 2025.pdf
├── HEALTHSENSE CAT COVER_SOB - FEB 2025.pdf
└── output_renewals/
    ├── [generated PDFs]
    └── [QR code files]
```

## Configuration Options

### Output Folder Customization
```bash
python healthcare_renewal_final.py --output custom_folder_name
```

### QR Code API Configuration
The system uses ZwennPay API for QR code generation:
- Merchant ID: 153
- API Endpoint: `https://api.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR`
- Timeout: 20 seconds

## Troubleshooting

### Common Issues
1. **Missing Excel file:** Ensure `RENEWAL_LISTING.xlsx` exists in root directory
2. **Font errors:** Verify font files exist in `fonts/` folder
3. **Logo missing:** Check all image files are present
4. **QR generation fails:** Verify internet connection and API availability
5. **PDF merge errors:** Ensure PyMuPDF is installed correctly

### Error Handling
- All scripts include comprehensive error handling
- Backup files are created before modifications
- Processing continues even if individual files fail
- Detailed error messages guide troubleshooting

## Output Quality
- **PDF Resolution:** Optimized for print quality
- **Font Rendering:** Professional Cambria fonts
- **Logo Quality:** High-resolution scaling
- **QR Codes:** High contrast for reliable scanning
- **Layout:** Window envelope compatible addressing

## Security Considerations
- Customer data handled locally
- QR codes contain payment information
- Backup files created for data safety
- No sensitive data transmitted except for QR generation

## Maintenance
- Update logo files as needed
- Refresh form PDFs when policy terms change
- Monitor QR code API availability
- Regular testing with sample data recommended

---

*Last Updated: September 2025*
*System Version: Healthcare Renewal v2.0*