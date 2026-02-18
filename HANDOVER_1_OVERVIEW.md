# NICL Letter Generation System - Project Handover Documentation
## Part 1: System Overview & Architecture

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Project Status**: Production (Live on VPS)  
**Production URL**: https://arrears.niclmauritius.site  
**Short URL Domain**: https://nicl.ink

---

## 📋 Executive Summary

The NICL Letter Generation System is a web-based application that automates the creation, distribution, and tracking of insurance policy arrears notices for National Insurance Company Limited (NICL) Mauritius.

### Key Capabilities
- **PDF Generation**: Creates personalized arrears letters from Excel data (5000+ records)
- **SMS Notifications**: Generates custom short URLs (nicl.ink) for mobile access
- **Email Notifications**: Automated completion alerts via Brevo API
- **QR Code Integration**: Payment QR codes via ZwennPay API
- **Batch Processing**: Handles large datasets with progress tracking
- **Multi-Template Support**: 5 different letter templates (SPH, JPH, Company, MED variants)

### Technology Stack
- **Frontend**: React 18 + Vite + TailwindCSS
- **Backend**: Node.js (Express) + Python 3.9+
- **PDF Generation**: ReportLab + PyMuPDF
- **Server**: Ubuntu VPS with Nginx + PM2
- **APIs**: ZwennPay (QR codes), Brevo (emails)

---

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser (React)                      │
│  https://arrears.niclmauritius.site                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Nginx (Reverse Proxy)                       │
│  - SSL Termination (Let's Encrypt)                          │
│  - Static File Serving                                       │
│  - Request Routing                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Node.js Server (Express)                        │
│  Port: 3001 (PM2 managed)                                   │
│  - API Endpoints                                             │
│  - File Upload Handling                                      │
│  - Python Script Execution                                   │
│  - Short URL Redirects (nicl.ink)                           │
└────────┬────────────────────────────────┬──────────────────┘
         │                                 │
         ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│  Python Scripts      │      │  External APIs               │
│  (venv isolated)     │      │  - ZwennPay (QR codes)      │
│  - PDF Generation    │      │  - Brevo (Email)            │
│  - SMS Link Gen      │      │  - TinyURL (legacy)         │
│  - PDF Combining     │      └──────────────────────────────┘
└──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    File System Storage                       │
│  - output_*/ (Generated PDFs)                               │
│  - letter_links/ (SMS link data)                            │
│  - temp_uploads/ (Temporary Excel files)                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Frontend (React Application)
**Location**: `/src/`  
**Build Output**: `/dist/`

**Key Components**:
- `App.jsx` - Main application container
- `TabNavigation.jsx` - Tab switching interface
- `PDFGenerationSection.jsx` - PDF generation UI
- `FolderBasedSMSSection.jsx` - SMS link generation
- `EmailConfigSection.jsx` - Email notification settings
- `FileBrowser.jsx` - PDF folder browsing
- `DownloadProgress.jsx` - Progress tracking

**Features**:
- Responsive design (mobile-first)
- Real-time progress tracking
- File upload with validation
- Dynamic API base URL detection

#### 2. Backend (Node.js Server)
**Location**: `server.js`  
**Port**: 3001  
**Process Manager**: PM2

**Core Responsibilities**:
- API endpoint handling
- File upload management (50MB limit)
- Python script execution
- Short URL redirect service
- Static file serving

**Key API Endpoints**:
```
POST /api/generate-pdfs              - Generate PDF letters
POST /api/combine-pdfs               - Combine PDFs into single file
POST /api/generate-sms-links         - Generate SMS notification links
POST /api/generate-sms-links-from-folder - Folder-based SMS generation
GET  /api/folders                    - List PDF output folders
GET  /api/pdf/:filename              - Download PDF file
GET  /api/download-sms-file/:folder  - Download SMS CSV file
GET  /letter/:uniqueId               - Customer letter viewer
GET  /:shortId                       - Short URL redirect (nicl.ink)
POST /api/set-user-email             - Configure email notifications
GET  /api/get-user-email             - Get email configuration
```

#### 3. Python Scripts
**Location**: Root directory  
**Environment**: Virtual environment (`venv/`)

**PDF Generation Templates**:
1. `SPH_Fresh.py` - Single Policy Holder (Life Insurance)
2. `JPH_Fresh.py` - Joint Policy Holder (Life Insurance)
3. `Company_Fresh.py` - Company policies
4. `MED_SPH_Fresh_Signature.py` - Medical Single Policy Holder
5. `MED_JPH_Fresh_Signature.py` - Medical Joint Policy Holder

**Utility Scripts**:
- `pdf_generator_wrapper.py` - Orchestrates PDF generation
- `combine_pdfs.py` - Merges PDFs (uses PyMuPDF)
- `generate_sms_links.py` - Creates SMS notification links
- `completion_email_service.py` - Sends completion emails
- `brevo_email_service.py` - Brevo API integration

---

## 📁 Project Structure

```
/var/www/pdf-generator/
├── server.js                    # Node.js backend server
├── package.json                 # Node dependencies
├── vite.config.js              # Vite build configuration
├── tailwind.config.js          # TailwindCSS configuration
├── .env                        # Environment variables (NOT in Git)
├── requirements.txt            # Python dependencies
│
├── src/                        # React frontend source
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   └── components/
│       ├── TabNavigation.jsx
│       ├── PDFGenerationSection.jsx
│       ├── FolderBasedSMSSection.jsx
│       ├── EmailConfigSection.jsx
│       ├── FileBrowser.jsx
│       └── DownloadProgress.jsx
│
├── dist/                       # Built frontend (production)
│
├── venv/                       # Python virtual environment
│   ├── bin/python
│   └── lib/python3.x/site-packages/
│
├── Python Scripts (PDF Generation)
│   ├── SPH_Fresh.py
│   ├── JPH_Fresh.py
│   ├── Company_Fresh.py
│   ├── MED_SPH_Fresh_Signature.py
│   ├── MED_JPH_Fresh_Signature.py
│   ├── pdf_generator_wrapper.py
│   ├── combine_pdfs.py
│   ├── generate_sms_links.py
│   ├── completion_email_service.py
│   └── brevo_email_service.py
│
├── Assets
│   ├── fonts/                  # Font files for PDFs
│   ├── NICLOGO2.jpg           # Company logo
│   ├── maucas2.jpeg           # MauCAS logo
│   └── zwennPay.jpg           # ZwennPay logo
│
├── Generated Content (NOT in Git)
│   ├── output_*/              # PDF output folders
│   ├── letter_links/          # SMS link JSON data
│   ├── temp_uploads/          # Temporary Excel uploads
│   └── url_mappings.json      # Short URL mappings
│
└── Documentation
    ├── HOW_TO_USE.md
    ├── DEPLOYMENT_GUIDE.md
    ├── VPS_UPDATE_GUIDE_SMS_EMAIL.md
    ├── NICL_CUSTOM_URL_SHORTENER_SPECIFICATION.md
    └── PROJECT_HANDOVER_DOCUMENTATION.md (this file)
```

---

## 🔐 Environment Variables

**Location**: `/var/www/pdf-generator/.env` (VPS)  
**⚠️ CRITICAL**: Never commit .env to Git

```bash
# Email Configuration (Brevo)
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=system@niclmauritius.site
SENDER_NAME=NIC Mauritius System
REPLY_TO_EMAIL=support@niclmauritius.site
REPLY_TO_NAME=NIC Support

# User Email for Notifications
USER_EMAIL=admin@niclmauritius.site
USER_NAME=NICL Admin

# ZwennPay Configuration
ZWENNPAY_MERCHANT_ID=151

# Node Environment
NODE_ENV=production
PORT=3001
```

---

## 🌐 Domain Configuration

### Primary Domain: arrears.niclmauritius.site
- **Purpose**: Main application access
- **SSL**: Let's Encrypt (auto-renewal)
- **Nginx Config**: `/etc/nginx/sites-available/arrears.niclmauritius.site`

### Short URL Domain: nicl.ink
- **Purpose**: SMS notification short URLs
- **SSL**: Let's Encrypt (auto-renewal)
- **Nginx Config**: `/etc/nginx/sites-available/nicl.ink`
- **Redirect Service**: Handled by Node.js server
- **URL Format**: `https://nicl.ink/abc123` → `https://arrears.niclmauritius.site/letter/uniqueid`

---

## 📊 Data Flow

### PDF Generation Workflow
```
1. User uploads Excel file (Generic_Template.xlsx)
   ↓
2. Frontend sends to /api/generate-pdfs
   ↓
3. Server saves to temp_uploads/
   ↓
4. Server executes pdf_generator_wrapper.py
   ↓
5. Wrapper calls appropriate template (SPH_Fresh.py, etc.)
   ↓
6. Template reads Excel, generates PDFs with QR codes
   ↓
7. PDFs saved to output_*/protected/ and output_*/unprotected/
   ↓
8. Completion email sent (if configured)
   ↓
9. Frontend displays success + file count
```

### SMS Link Generation Workflow
```
1. User selects PDF folder from dropdown
   ↓
2. Frontend sends to /api/generate-sms-links-from-folder
   ↓
3. Server executes generate_sms_links.py
   ↓
4. Script reads Excel data + PDF files
   ↓
5. For each customer:
   - Creates unique letter ID
   - Generates custom short URL (nicl.ink)
   - Stores letter data as JSON
   - Creates SMS message
   ↓
6. Saves sms_batch.csv to letter_links/folder/
   ↓
7. Completion email sent (if configured)
   ↓
8. User downloads CSV for SMS gateway
```

### Customer Letter Access Workflow
```
1. Customer receives SMS with nicl.ink/abc123
   ↓
2. Customer clicks link
   ↓
3. Nginx routes to Node.js server
   ↓
4. Server looks up short ID in url_mappings.json
   ↓
5. Server redirects to /letter/uniqueid
   ↓
6. Server loads letter data from JSON
   ↓
7. Server generates mobile-friendly HTML
   ↓
8. Customer views letter + QR code
   ↓
9. Customer can download unprotected PDF
```

---

**Continue to Part 2: Installation & Deployment**