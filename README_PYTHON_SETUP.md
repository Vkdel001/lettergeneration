# PDF Generator with Python Templates

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (if not already installed)
pip install pandas requests segno reportlab
```

### 2. Start the Application

```bash
# Option 1: Start both frontend and backend together
npm run dev:full

# Option 2: Start them separately
# Terminal 1 - Backend server
npm run server

# Terminal 2 - Frontend development server  
npm run dev
```

### 3. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:3001

## How It Works

1. **Upload Excel File**: Upload your Excel file with policyholder data
2. **Select Template**: Choose from 4 Python PDF templates:
   - SPH Template
   - SPH Template (Aligned)
   - Company Template  
   - JPH Template
3. **Generate PDFs**: 
   - Python scripts generate PDFs in batch
   - Option to auto-download or send via email
4. **Email Processing**: Send generated PDFs as email attachments

## File Structure

```
├── server.js                              # Backend API server
├── pdf_generator_wrapper.py               # Python wrapper script
├── SPH_PDF_CREATION_4JunOk.py            # SPH template
├── SPH_PDF_CREATION_4JunOk_Alignment.py  # SPH aligned template
├── COMPANY_PDF_CREATION_4JunOk.py        # Company template
├── JPH_PDF_CREATION_4JunOk.py            # JPH template
├── temp_uploads/                          # Temporary Excel files
├── generated_pdfs/                        # Generated PDF output
└── src/App.jsx                            # Frontend React app
```

## Expected Excel Columns

Your Excel file should contain these columns:
- POLICYHOLDER_NAME
- POL_NO  
- EMAIL_ID (required for email functionality)
- ARREARS_AMOUNT
- POL_FROM_DT
- POL_TO_DT
- Address columns (POLICYHOLDER_ADDRESS_1, etc.)

## Troubleshooting

### Python Script Issues
- Ensure Python is installed and accessible via `python` command
- Check that all required Python packages are installed
- Verify your Python scripts work independently

### Backend Issues  
- Make sure port 3001 is available
- Check server logs for detailed error messages
- Ensure temp_uploads and generated_pdfs directories are writable

### Frontend Issues
- Verify backend is running on port 3001
- Check browser console for API errors
- Ensure EmailJS configuration is correct for email functionality