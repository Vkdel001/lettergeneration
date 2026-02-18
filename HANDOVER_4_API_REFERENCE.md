# NICL Letter Generation System - Project Handover Documentation
## Part 4: API Reference & Technical Details

---

## 📡 API Endpoints Reference

### PDF Generation APIs

#### POST /api/generate-pdfs
Generate PDF letters from Excel file.

**Request**:
```javascript
Content-Type: multipart/form-data

{
  excelFile: File,              // Excel file (Generic_Template.xlsx)
  template: String,             // Template name (e.g., "SPH_Fresh.py")
  outputFolder: String          // Optional custom output folder name
}
```

**Response Success (200)**:
```json
{
  "success": true,
  "message": "Processed 5000 records successfully (10000 files generated)",
  "files": [
    {
      "filename": "001_00920_0001414_John_Doe.pdf",
      "path": "/output_sph_December2025/protected/001_00920_0001414_John_Doe.pdf",
      "size": 245678,
      "location": "protected"
    }
  ],
  "recordsProcessed": 5000,
  "filesGenerated": 10000,
  "breakdown": {
    "protected": 5000,
    "unprotected": 5000,
    "main": 0
  }
}
```

**Response Error (500)**:
```json
{
  "success": false,
  "message": "Python script execution failed",
  "stdout": "...",
  "stderr": "...",
  "code": 1
}
```

**Timeout**: 6 hours (21600000 ms)

---

#### POST /api/combine-pdfs
Combine multiple PDFs into single file.

**Request**:
```json
{
  "folderName": "output_sph_December2025",
  "outputName": "SPH_Combined_December2025"
}
```

**Response Success (200)**:
```json
{
  "success": true,
  "message": "Combined 5000 unprotected PDFs successfully",
  "filename": "SPH_Combined_December2025.pdf",
  "folderPath": "output_sph_December2025/combined",
  "fullPath": "/var/www/pdf-generator/output_sph_December2025/combined/SPH_Combined_December2025.pdf",
  "pdfCount": 5000,
  "note": "Protected PDFs excluded (each has unique password)"
}
```

**Notes**:
- Only combines unprotected PDFs
- Protected PDFs have unique passwords (cannot be combined)
- Uses PyMuPDF for QR code preservation
- Timeout: 30 minutes

---

### SMS Link Generation APIs

#### POST /api/generate-sms-links-from-folder
Generate SMS notification links for existing PDF folder.

**Request**:
```json
{
  "folderName": "output_sph_December2025",
  "template": "SPH_Fresh.py",           // Optional (auto-detected)
  "baseUrl": "https://arrears.niclmauritius.site"  // Optional
}
```

**Response Success (200)**:
```json
{
  "success": true,
  "message": "Generated 5000 SMS links successfully from folder output_sph_December2025",
  "folderName": "output_sph_December2025",
  "template": "SPH_Fresh.py",
  "linksGenerated": 5000,
  "smsFileReady": true,
  "smsFilePath": "letter_links/output_sph_December2025/sms_batch.csv",
  "processingTime": "2m 15s",
  "excelFileUsed": "output_sph_December2025_source.xlsx"
}
```

**Timeout**: 10 minutes

---

#### GET /api/download-sms-file/:outputFolder
Download SMS batch CSV file.

**Request**:
```
GET /api/download-sms-file/output_sph_December2025
```

**Response**:
- Content-Type: text/csv
- Content-Disposition: attachment; filename="SMS_Batch_output_sph_December2025_2026-01-04.csv"

**CSV Format**:
```csv
Mobile,Message,ShortURL,Policy,CustomerName,Status
57123456,"Dear Mr Smith, your NICL arrears notice is ready. View online: https://nicl.ink/abc123 Valid for 30 days.",https://nicl.ink/abc123,00920/0001414,Mr John Smith,Ready
```

---

### Folder Management APIs

#### GET /api/folders
List available PDF output folders.

**Response**:
```json
{
  "success": true,
  "folders": [
    {
      "name": "output_sph_December2025",
      "pdfCount": 10000
    }
  ]
}
```

---

#### GET /api/pdf-folders-enhanced
Enhanced folder listing with SMS link status.

**Response**:
```json
{
  "success": true,
  "folders": [
    {
      "name": "output_sph_December2025",
      "template": "SPH_Fresh.py",
      "templateType": "SPH",
      "pdfCount": 5000,
      "protectedCount": 5000,
      "unprotectedCount": 5000,
      "createdDate": "2026-01-04T10:00:00.000Z",
      "lastModified": "2026-01-04T12:00:00.000Z",
      "status": "complete",
      "hasExcelFile": true,
      "hasFolderSpecificExcel": true,
      "excelFilePath": "output_sph_December2025_source.xlsx",
      "smsLinksGenerated": true,
      "smsLinksCount": 5000,
      "smsFileExists": true,
      "smsLinksUpToDate": true
    }
  ],
  "totalFolders": 1
}
```

---

### Letter Viewer APIs

#### GET /letter/:uniqueId
Customer-facing letter viewer.

**Request**:
```
GET /letter/7e89984128160d9b
```

**Response**: HTML page with:
- Customer letter content
- Policy details table
- QR code for payment
- Download PDF button
- Mobile-responsive design

**Access Control**:
- Checks expiry date (30 days)
- Tracks access count (max 10 views)
- Increments view counter

---

#### GET /:shortId
Short URL redirect service (nicl.ink).

**Request**:
```
GET /abc123
```

**Response**: 301 Redirect to full letter URL

**Logic**:
1. Validates short ID format (6 chars, lowercase + digits)
2. Looks up in url_mappings.json
3. Checks expiry and active status
4. Increments click counter
5. Redirects to full URL

**Skip Patterns** (not processed as short URLs):
- api, letter, health, favicon.ico, robots.txt
- Any path with file extension
- Paths not matching 6-character format

---

### Email Configuration APIs

#### POST /api/set-user-email
Configure user email for notifications.

**Request**:
```json
{
  "email": "admin@niclmauritius.site",
  "name": "NICL Admin"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Email configuration saved successfully"
}
```

---

#### GET /api/get-user-email
Get current email configuration.

**Response**:
```json
{
  "success": true,
  "email": "admin@niclmauritius.site",
  "name": "NICL Admin"
}
```

---

### Utility APIs

#### GET /api/status
Server health check.

**Response**:
```json
{
  "status": "running",
  "timestamp": "2026-01-04T13:42:51.708Z",
  "outputDir": "/var/www/pdf-generator/generated_pdfs"
}
```

---

#### GET /api/templates
List available PDF templates.

**Response**:
```json
{
  "success": true,
  "templates": [
    {
      "filename": "SPH_Fresh.py",
      "displayName": "SPH_Fresh.py"
    },
    {
      "filename": "JPH_Fresh.py",
      "displayName": "JPH_Fresh.py"
    }
  ]
}
```

---

## 🔧 Python Scripts Reference

### PDF Generation Templates

#### SPH_Fresh.py
**Purpose**: Single Policy Holder - Life Insurance  
**Excel Columns Required**:
- Policy No, Owner 1 Title, Owner 1 First Name, Owner 1 Surname
- Owner 1 Policy Address 1-4
- Arrears Amount, Computed Gross Premium, Frequency
- Arrears Processing Date
- MOBILE_NO, NIC

**Output**:
- Protected PDF: `{seq}_{policy}_{name}.pdf` (password: NIC)
- Unprotected PDF: Same filename (no password)

**Features**:
- QR code generation via ZwennPay API
- Sequence numbering for proper ordering
- NaN handling for missing names
- Multi-strategy date parsing

---

#### JPH_Fresh.py
**Purpose**: Joint Policy Holder - Life Insurance  
**Additional Columns**:
- Owner 2 Title, Owner 2 First Name, Owner 2 Surname

**Output**: Same as SPH but with joint names

---

#### Company_Fresh.py
**Purpose**: Company/Corporate policies  
**Excel Columns**:
- Company Name instead of individual names
- Same other fields as SPH

---

#### MED_SPH_Fresh_Signature.py
**Purpose**: Medical/Health Insurance - Single Policy Holder  
**Differences**:
- Different letter content (health-specific)
- Different subject line
- Same technical implementation as SPH

---

#### MED_JPH_Fresh_Signature.py
**Purpose**: Medical/Health Insurance - Joint Policy Holder  
**Differences**: Same as MED_SPH but with joint names

---

### Utility Scripts

#### pdf_generator_wrapper.py
**Purpose**: Orchestrates PDF generation process

**Functions**:
- Validates Excel file
- Executes appropriate template
- Handles errors and logging
- Sends completion email
- Cleans up temporary files

**Usage**:
```bash
python pdf_generator_wrapper.py \
  --template SPH_Fresh.py \
  --input Generic_Template.xlsx \
  --output output_sph_December2025
```

---

#### combine_pdfs.py
**Purpose**: Combines multiple PDFs into single file

**Features**:
- Uses PyMuPDF for image preservation
- Falls back to PyPDF2 if PyMuPDF unavailable
- Processes unprotected PDFs only
- Maintains sequence order

**Usage**:
```bash
python combine_pdfs.py \
  --folder output_sph_December2025 \
  --name SPH_Combined_December2025 \
  --output output_sph_December2025/combined/SPH_Combined_December2025.pdf
```

---

#### generate_sms_links.py
**Purpose**: Generates SMS notification links

**Functions**:
- Reads Excel data
- Creates unique letter IDs
- Generates custom short URLs (nicl.ink)
- Stores letter data as JSON
- Creates SMS batch CSV
- Sends completion email

**Usage**:
```bash
python generate_sms_links.py \
  --folder output_sph_December2025 \
  --template SPH_Fresh.py \
  --base-url https://arrears.niclmauritius.site
```

---

#### completion_email_service.py
**Purpose**: Sends completion notification emails

**Email Types**:
1. PDF Generation Complete
2. SMS Links Generation Complete

**Usage**:
```bash
python completion_email_service.py \
  --type pdf \
  --email admin@niclmauritius.site \
  --name "NICL Admin" \
  --folder output_sph_December2025 \
  --count 5000 \
  --time "15m 30s" \
  --template SPH
```

---

## 📊 Data Formats

### Excel Input Format (Generic_Template.xlsx)

**Required Columns**:
```
Policy No | Owner 1 Title | Owner 1 First Name | Owner 1 Surname |
Owner 1 Policy Address 1 | Owner 1 Policy Address 2 |
Owner 1 Policy Address 3 | Owner 1 Policy Address 4 |
Arrears Amount | Computed Gross Premium | Frequency |
Arrears Processing Date | MOBILE_NO | NIC
```

**Optional Columns** (for JPH):
```
Owner 2 Title | Owner 2 First Name | Owner 2 Surname
```

**Data Types**:
- Policy No: Text (e.g., "00920/0001414")
- Names: Text
- Addresses: Text
- Amounts: Number (e.g., 439.17)
- Frequency: Text (e.g., "Quarterly", "Monthly")
- Date: Date or Excel serial number
- Mobile: Text (e.g., "57123456")
- NIC: Text (e.g., "A1234567890123")

---

### URL Mappings Format (url_mappings.json)

```json
{
  "abc123": {
    "url": "https://arrears.niclmauritius.site/letter/7e89984128160d9b",
    "created": "2026-01-04T13:07:10.458Z",
    "expires": "2026-02-03T13:07:10.470Z",
    "clicks": 5,
    "active": true,
    "lastAccessed": "2026-01-04T15:30:00.000Z"
  }
}
```

---

### Letter Data Format (letter_links/{folder}/{uniqueId}.json)

```json
{
  "id": "7e89984128160d9b",
  "customerName": "Mr John Smith",
  "policyNo": "00920/0001414",
  "mobileNo": "57123456",
  "nic": "A1234567890123",
  "date": "30-December-2025",
  "address": [
    "MORCELLEMENT CHAVRY",
    "BOIS PIGNOLET",
    "TERRE ROUGE"
  ],
  "salutation": "Dear Mr John Smith,",
  "subject": "RE: ARREARS ON YOUR LIFE INSURANCE POLICY",
  "letterType": "Life Insurance",
  "bodyIntro": "At NIC, we value the trust...",
  "policyDetails": {
    "policyNo": "00920/0001414",
    "premium": "MUR 439.17",
    "frequency": "Quarterly",
    "arrearsAmount": "MUR 439.17"
  },
  "templateType": "SPH",
  "qrCodeData": "00020101021...",
  "rowIndex": 0,
  "createdAt": "2026-01-04T13:07:10.458Z",
  "expiresAt": "2026-02-03T13:07:10.470Z",
  "accessCount": 2,
  "maxAccess": 10,
  "isActive": true,
  "pdfPath": "/output_sph_December2025/protected/001_00920_0001414_Mr_John_Smith.pdf"
}
```

---

**Continue to Part 5: Known Issues & Future Enhancements**