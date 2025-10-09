import React, { useState, useCallback, useEffect } from 'react';
import { Upload, FileText, Download, AlertCircle, CheckCircle, Loader, Mail, Settings, LogOut } from 'lucide-react';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import QRCode from 'qrcode';
import emailjs from '@emailjs/browser';
import sicomLogo from './nic2.jpeg'; // Ensure this file exists
import AuthScreen from './components/AuthScreen.jsx';
import TabNavigation from './components/TabNavigation.jsx';
import DownloadProgress from './components/DownloadProgress.jsx';
import FileBrowser from './components/FileBrowser.jsx';

// Dynamic API URL - works both locally and on VPS
const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:3001'
  : `http://${window.location.hostname}:3001`;

const PDFGenerator = () => {
  // Authentication state (temporarily disabled for local testing)
  const [isAuthenticated, setIsAuthenticated] = useState(true); // TEMP: Skip auth for testing
  const [authToken, setAuthToken] = useState('test-token');
  const [userEmail, setUserEmail] = useState('test@local.dev');

  // Existing state
  const [file, setFile] = useState(null);
  const [data, setData] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [autoDownload, setAutoDownload] = useState(true);
  const [sendEmails, setSendEmails] = useState(false);
  const [emailProgress, setEmailProgress] = useState(0);
  const [emailResults, setEmailResults] = useState([]);
  const [batchSize, setBatchSize] = useState(10);
  const [concurrentLimit, setConcurrentLimit] = useState(3);
  const [processedCount, setProcessedCount] = useState(0);
  const [failedCount, setFailedCount] = useState(0);
  const [currentBatch, setCurrentBatch] = useState(0);
  const [totalBatches, setTotalBatches] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState('SPH_Fresh.py');
  const [availableTemplates, setAvailableTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  // Removed mode state - using workflow-based UI instead
  const [selectedFolder, setSelectedFolder] = useState('');
  const [availableFolders, setAvailableFolders] = useState([]);
  const [combinedPdfName, setCombinedPdfName] = useState('');
  // Removed pdfGenerationMethod - only using Python now
  const [pythonProgress, setPythonProgress] = useState(0);
  const [generatedPdfPaths, setGeneratedPdfPaths] = useState([]);
  const [emailConfig, setEmailConfig] = useState({
    serviceId: 'service_3uano3i',
    templateId: 'template_683qa5q',
    publicKey: '6IXn9qDThhQLQKdjt'
  });
  const [showEmailConfig, setShowEmailConfig] = useState(false);

  // UI state for enhanced interface
  const [activeTab, setActiveTab] = useState('combine');
  const [showDownloadProgress, setShowDownloadProgress] = useState(false);
  const [downloadInfo, setDownloadInfo] = useState(null);

  // Check for existing authentication on component mount (DISABLED FOR TESTING)
  /*
  useEffect(() => {
    const checkExistingAuth = () => {
      const token = sessionStorage.getItem('authToken');
      const email = sessionStorage.getItem('userEmail');
      const authTime = sessionStorage.getItem('authTime');
      
      if (token && email && authTime) {
        // Check if session is still valid (8 hours)
        const sessionAge = Date.now() - parseInt(authTime);
        const maxAge = 8 * 60 * 60 * 1000; // 8 hours
        
        if (sessionAge < maxAge) {
          setAuthToken(token);
          setUserEmail(email);
          setIsAuthenticated(true);
          console.log(`[AUTH] Restored session for ${email}`);
        } else {
          // Session expired, clear storage
          sessionStorage.removeItem('authToken');
          sessionStorage.removeItem('userEmail');
          sessionStorage.removeItem('authTime');
          console.log('[AUTH] Session expired, cleared storage');
        }
      }
    };
    
    checkExistingAuth();
  }, []);
  */

  // Initialize EmailJS
  useEffect(() => {
    if (emailConfig.publicKey) {
      emailjs.init(emailConfig.publicKey);
    }
  }, [emailConfig.publicKey]);

  // Authentication functions
  const handleAuthenticated = (token, email) => {
    setAuthToken(token);
    setUserEmail(email);
    setIsAuthenticated(true);
    console.log(`[AUTH] User authenticated: ${email}`);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('userEmail');
    sessionStorage.removeItem('authTime');
    setAuthToken(null);
    setUserEmail('');
    setIsAuthenticated(false);
    console.log('[AUTH] User logged out');
  };

  // Helper function to get auth headers
  const getAuthHeaders = () => {
    return authToken ? {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    } : {
      'Content-Type': 'application/json'
    };
  };

  // Fetch available templates and folders on component mount
  useEffect(() => {
    if (!isAuthenticated || !authToken) {
      return; // Don't fetch if not authenticated
    }

    const fetchTemplates = async () => {
      console.log('[DEBUG] Starting template fetch, setting loading to true');
      setTemplatesLoading(true);
      try {
        const response = await fetch(`${API_BASE}/api/templates`);
        const data = await response.json();
        console.log('[DEBUG] Server response for templates:', data);
        if (data.success) {
          console.log('[DEBUG] Available templates from server:', data.templates.map(t => t.filename));
          setAvailableTemplates(data.templates);
          // Set first template as default if no template is selected
          if (data.templates.length > 0) {
            console.log('[DEBUG] Setting default template to:', data.templates[0].filename);
          }
        }
      } catch (error) {
        console.error('Failed to fetch templates:', error);
        console.log('[DEBUG] Using fallback templates');
        // Fallback to hardcoded templates
        setAvailableTemplates([
          { filename: 'SPH_Fresh.py', displayName: 'SPH Template' },
          { filename: 'JPH_Fresh.py', displayName: 'JPH Template' },
          { filename: 'Company_Fresh.py', displayName: 'Company Template' },
          { filename: 'MED_SPH_Fresh_Signature.py', displayName: 'MED SPH Template (with Signature)' },
          { filename: 'MED_JPH_Fresh_Signature.py', displayName: 'MED JPH Template (with Signature)' }
        ]);
      } finally {
        console.log('[DEBUG] Template fetch complete, setting loading to false');
        setTemplatesLoading(false);
      }
    };

    const fetchFolders = async () => {
      try {
        console.log('[DEBUG] Fetching folders...');
        const response = await fetch(`${API_BASE}/api/folders`);
        const data = await response.json();
        console.log('[DEBUG] Folders response:', data);
        if (data.success) {
          console.log('[DEBUG] Available folders:', data.folders);
          setAvailableFolders(data.folders);
        } else {
          console.error('Failed to fetch folders:', data.message);
        }
      } catch (error) {
        console.error('Failed to fetch folders:', error);
      }
    };

    fetchTemplates();
    fetchFolders();
  }, [isAuthenticated, authToken]);

  // Function to get previous month name and year
  const getPreviousMonthFolder = () => {
    const now = new Date();
    const previousMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const monthName = previousMonth.toLocaleString('default', { month: 'long' });
    const year = previousMonth.getFullYear();
    return `${monthName}${year}`;
  };

  // Function to generate output folder name based on Excel filename
  const getOutputFolderName = (filename) => {
    const lowerFilename = filename.toLowerCase();
    const previousMonthYear = getPreviousMonthFolder();

    if (lowerFilename === 'output_sph.xlsx') {
      return `output_sph_${previousMonthYear}`;
    } else if (lowerFilename === 'output_jph.xlsx') {
      return `output_JPH_${previousMonthYear}`;
    } else if (lowerFilename === 'output_company_sph.xlsx') {
      return `output_company_sph_${previousMonthYear}`;
    } else if (lowerFilename === 'output_sph_med.xlsx') {
      return `output_sph_MED_${previousMonthYear}`;
    } else if (lowerFilename === 'output_jph_med.xlsx') {
      return `output_JPH_MED_${previousMonthYear}`;
    }

    return `default_${previousMonthYear}`;
  };

  // Function to automatically select template based on Excel filename
  const getTemplateForFile = (filename) => {
    const lowerFilename = filename.toLowerCase();

    // Exact mappings as specified:
    // output_sph.xlsx → SPH_Fresh.py
    // output_JPH.xlsx → JPH_Fresh.py  
    // output_company_sph.xlsx → Company_Fresh.py
    // output_sph_MED.xlsx → MED_SPH_Fresh_Signature.py
    // output_JPH_MED.xlsx → MED_JPH_Fresh_Signature.py

    if (lowerFilename === 'output_sph.xlsx') {
      return 'SPH_Fresh.py';
    } else if (lowerFilename === 'output_jph.xlsx') {
      return 'JPH_Fresh.py';
    } else if (lowerFilename === 'output_company_sph.xlsx') {
      return 'Company_Fresh.py';
    } else if (lowerFilename === 'output_sph_med.xlsx') {
      return 'MED_SPH_Fresh_Signature.py';
    } else if (lowerFilename === 'output_jph_med.xlsx') {
      return 'MED_JPH_Fresh_Signature.py';
    }

    return null; // No automatic selection for other files
  };

  // Function to validate file and template combination
  const validateFileTemplateCombo = () => {
    if (!file) return { isValid: true, message: '' };

    const expectedTemplate = getTemplateForFile(file.name);
    if (!expectedTemplate) {
      return {
        isValid: true,
        message: 'No specific template required for this file. You can select any template.'
      };
    }

    if (selectedTemplate !== expectedTemplate) {
      return {
        isValid: false,
        message: `Warning: For file "${file.name}", the recommended template is "${expectedTemplate}". Current selection: "${selectedTemplate}"`
      };
    }

    return {
      isValid: true,
      message: `✓ Correct template selected for "${file.name}"`
    };
  };

  const handleFileUpload = useCallback(async (event) => {
    const uploadedFile = event.target.files[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setError('');

    // Auto-select template based on filename
    const autoSelectedTemplate = getTemplateForFile(uploadedFile.name);
    console.log(`[DEBUG] File: "${uploadedFile.name}" -> Template: "${autoSelectedTemplate}"`);

    if (autoSelectedTemplate) {
      console.log('[DEBUG] Templates loading state:', templatesLoading, 'Available templates count:', availableTemplates.length);

      // If no templates are available yet, try to fetch them again or use fallback
      if (availableTemplates.length === 0) {
        console.log('[DEBUG] No templates available, using fallback list');
        // Use the fallback templates directly
        const fallbackTemplates = [
          { filename: 'SPH_Fresh.py', displayName: 'SPH Template' },
          { filename: 'JPH_Fresh.py', displayName: 'JPH Template' },
          { filename: 'Company_Fresh.py', displayName: 'Company Template' },
          { filename: 'MED_SPH_Fresh_Signature.py', displayName: 'MED SPH Template (with Signature)' },
          { filename: 'MED_JPH_Fresh_Signature.py', displayName: 'MED JPH Template (with Signature)' }
        ];

        setAvailableTemplates(fallbackTemplates);

        // Check if the template exists in fallback templates
        const templateExists = fallbackTemplates.find(t => t.filename === autoSelectedTemplate);
        if (templateExists) {
          setSelectedTemplate(autoSelectedTemplate);
          console.log(`Auto-selected template from fallback: ${autoSelectedTemplate} for file: ${uploadedFile.name}`);
        } else {
          console.error(`Template ${autoSelectedTemplate} not found in fallback templates`);
          setError(`Required template "${autoSelectedTemplate}" not found for file "${uploadedFile.name}". Please ensure the correct Python template files are available.`);
          return;
        }
      } else {
        // Check if the template exists in available templates
        const templateExists = availableTemplates.find(t => t.filename === autoSelectedTemplate);
        if (templateExists) {
          setSelectedTemplate(autoSelectedTemplate);
          console.log(`Auto-selected template: ${autoSelectedTemplate} for file: ${uploadedFile.name}`);
        } else {
          console.error(`Template ${autoSelectedTemplate} not found in available templates`);
          console.log(`Available templates:`, availableTemplates.map(t => t.filename));
          setError(`Required template "${autoSelectedTemplate}" not found for file "${uploadedFile.name}". Please ensure the correct Python template files are available.`);
          return; // Stop processing
        }
      }
    } else {
      console.error(`No template mapping found for: ${uploadedFile.name}`);
      setError(`Unsupported file format: "${uploadedFile.name}". Please use one of the supported formats: output_sph.xlsx, output_JPH.xlsx, output_company_sph.xlsx, output_sph_MED.xlsx, or output_JPH_MED.xlsx`);
      return; // Stop processing
    }

    try {
      console.log('[DEBUG] File upload details:', {
        fileName: uploadedFile.name,
        fileSize: uploadedFile.size,
        fileType: uploadedFile.type,
        lastModified: new Date(uploadedFile.lastModified).toISOString()
      });

      const buffer = await uploadedFile.arrayBuffer();
      console.log('[DEBUG] File read as ArrayBuffer, size:', buffer.byteLength);

      const workbook = XLSX.read(buffer, { type: 'buffer' });
      console.log('[DEBUG] Workbook sheets:', workbook.SheetNames);

      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      console.log('[DEBUG] Parsed Excel data:', {
        rowCount: jsonData.length,
        firstRowKeys: Object.keys(jsonData[0] || {}),
        sampleRow: jsonData[0]
      });

      // Special check for EMAIL_ID column issue
      const hasEmailId = Object.keys(jsonData[0] || {}).includes('EMAIL_ID');
      console.log('[DEBUG] EMAIL_ID column check:', {
        hasEmailId: hasEmailId,
        allColumns: Object.keys(jsonData[0] || {}),
        expectedFile: 'output_sph.xlsx should have EMAIL_ID'
      });

      if (!hasEmailId) {
        console.warn('[WARNING] The uploaded file does not contain EMAIL_ID column');
        console.warn('[WARNING] Expected columns should include: EMAIL_ID, Policy No, Arrears Amount');
        console.warn('[WARNING] Please verify you are uploading the correct output_sph.xlsx file');
      }

      // Validate required columns for Generic_template.xlsx format (flexible matching)
      const requiredColumns = ['Policy No', 'Arrears Amount', 'EMAIL_ID'];
      const optionalColumns = ['Owner 1 Title', 'Owner 1 First Name', 'Owner 1 Surname', 'Owner 1 Policy Address 1'];

      const availableColumns = Object.keys(jsonData[0] || {});

      // Flexible column matching (case-insensitive and trimmed)
      const normalizeColumnName = (name) => name.toString().trim().toLowerCase().replace(/\s+/g, ' ');
      const normalizedAvailable = availableColumns.map(col => ({
        original: col,
        normalized: normalizeColumnName(col)
      }));

      const missingColumns = [];
      const foundColumns = [];

      requiredColumns.forEach(reqCol => {
        const normalizedReq = normalizeColumnName(reqCol);
        const found = normalizedAvailable.find(avail => avail.normalized === normalizedReq);

        if (found) {
          foundColumns.push(found.original);
        } else {
          // Try partial matching for common variations
          const partialMatch = normalizedAvailable.find(avail =>
            avail.normalized.includes('email') && normalizedReq.includes('email') ||
            avail.normalized.includes('policy') && normalizedReq.includes('policy') ||
            avail.normalized.includes('arrears') && normalizedReq.includes('arrears')
          );

          if (partialMatch) {
            foundColumns.push(partialMatch.original);
            console.log(`[INFO] Using column "${partialMatch.original}" for required "${reqCol}"`);
          } else {
            missingColumns.push(reqCol);
          }
        }
      });

      if (missingColumns.length > 0) {
        console.error('[ERROR] Available columns:', availableColumns);
        console.error('[ERROR] Missing required columns:', missingColumns);
        console.error('[ERROR] File info:', {
          fileName: file?.name,
          fileSize: file?.size,
          fileType: file?.type,
          lastModified: file?.lastModified ? new Date(file.lastModified).toISOString() : 'unknown'
        });
        console.error('[ERROR] First few rows of data:', jsonData.slice(0, 3));

        // For EMAIL_ID specifically, let's be more flexible
        if (missingColumns.includes('EMAIL_ID')) {
          console.warn('[WARNING] EMAIL_ID column missing - this may cause issues with email functionality');
          console.warn('[WARNING] Proceeding anyway, but email features may not work');
          // Remove EMAIL_ID from missing columns to allow processing
          const otherMissing = missingColumns.filter(col => col !== 'EMAIL_ID');
          if (otherMissing.length === 0) {
            console.warn('[WARNING] Only EMAIL_ID was missing, allowing file to proceed');
          } else {
            throw new Error(`Missing critical columns: ${otherMissing.join(', ')}. Available columns: ${availableColumns.join(', ')}`);
          }
        } else {
          throw new Error(`Missing required columns: ${missingColumns.join(', ')}. Available columns: ${availableColumns.join(', ')}`);
        }
      }

      console.log('Available columns:', availableColumns);
      console.log('Required columns found:', requiredColumns.filter(col => availableColumns.includes(col)));

      setData(jsonData);
      console.log('Parsed data:', jsonData);
    } catch (err) {
      setError('Error reading Excel file: ' + err.message);
    }
  }, []);

  const generateQRCode = async (amount) => {
    console.log('Generating QR code for amount:', amount);
    try {
      // Validate amount
      if (!amount || isNaN(amount) || amount <= 0) {
        throw new Error('Invalid amount for QR code generation');
      }

      const payload = {
        MerchantId: 57,
        SetTransactionAmount: true,
        TransactionAmount: String(amount),
        SetConvenienceIndicatorTip: false,
        ConvenienceIndicatorTip: 0,
        SetConvenienceFeeFixed: false,
        ConvenienceFeeFixed: 0,
        SetConvenienceFeePercentage: false,
        ConvenienceFeePercentage: 0,
      };

      const response = await fetch(
        'https://apiuat.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR',
        {
          method: 'POST',
          headers: {
            'accept': 'text/plain',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      console.log('API response status:', response.status);
      if (response.ok) {
        const qrData = await response.text();
        console.log('QR data received:', qrData);
        if (qrData && qrData.trim() && !['null', 'none', 'nan'].includes(qrData.toLowerCase())) {
          const qrDataUrl = await QRCode.toDataURL(qrData, {
            errorCorrectionLevel: 'L',
            width: 200,
            margin: 2,
          });
          console.log('QR code generated successfully:', qrDataUrl.substring(0, 50) + '...');
          return qrDataUrl;
        }
        throw new Error('Invalid QR response data');
      }
      throw new Error(`API request failed with status ${response.status}`);
    } catch (err) {
      console.error('QR generation failed:', err.message);
      return null; // Fallback to no QR code
    }
  };

  const formatDate = (date) => {
    try {
      const parsedDate = new Date(date);
      if (isNaN(parsedDate)) throw new Error('Invalid date');
      return parsedDate.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      });
    } catch {
      return 'N/A';
    }
  };

  const addDaysToDate = (date, days) => {
    try {
      const parsedDate = new Date(date);
      if (isNaN(parsedDate)) throw new Error('Invalid date');
      const result = new Date(parsedDate);
      result.setDate(parsedDate.getDate() + days);
      return result;
    } catch {
      return new Date();
    }
  };

  const generatePDF = async (rowData) => {
    const doc = new jsPDF();

    const policyholderName = `${rowData['Owner 1 Title'] || ''} ${rowData['Owner 1 First Name'] || ''} ${rowData['Owner 1 Surname'] || ''}`.trim();
    const address1 = rowData['Owner 1 Policy Address 1'] || '';
    const address2 = rowData['Owner 1 Policy Address 2'] || '';
    const address3 = rowData['Owner 1 Policy Address 3'] || '';
    const address4 = rowData['Owner 1 Policy Address 4'] || '';
    const policyNo = rowData['Policy No'] || '';
    const arrearsAmount = parseFloat(rowData['Arrears Amount']) || 0;
    const polFromDt = ''; // Not available in Generic_template.xlsx
    const polToDt = '';   // Not available in Generic_template.xlsx

    const currentDate = new Date();
    const letterDate = formatDate(currentDate);
    const dueDate = formatDate(addDaysToDate(currentDate, 10));

    doc.setFont('times', 'normal');
    let yPos = 15;
    const leftMargin = 15;
    const rightMargin = 195;

    doc.addImage(sicomLogo, 'PNG', 147, 5, 48, 20);

    const qrDataUrl = await generateQRCode(arrearsAmount);
    if (qrDataUrl) {
      doc.addImage(qrDataUrl, 'PNG', 154, 28, 33, 33);
    }

    doc.setFontSize(11);
    doc.text(letterDate, leftMargin, yPos);
    yPos += 15;

    if (policyholderName) {
      doc.text(policyholderName.toUpperCase(), leftMargin, yPos);
      yPos += 4;
    }

    const addressLines = [address1, address2, address3, address4].filter(line => line && line.trim());
    addressLines.forEach(line => {
      if (line.trim()) {
        doc.text(line.toUpperCase(), leftMargin, yPos);
        yPos += 4;
      }
    });
    yPos += 10;

    doc.text('Dear Valued Customer', leftMargin, yPos);
    yPos += 12;

    doc.setFont('times', 'bold');
    doc.setFontSize(11);
    const subjectText = `RE: FIRST NOTICE ARREARS ON HEALTH INSURANCE POLICY - ${policyNo}`;
    doc.text(subjectText, leftMargin, yPos);
    yPos += 12;

    doc.setFont('times', 'normal');
    doc.setFontSize(11);

    const para1 = 'We are writing to you with regards to the aforementioned Insurance Policy and we have noticed that there remains an outstanding amount due.';
    const para1Lines = doc.splitTextToSize(para1, rightMargin - leftMargin);
    para1Lines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 6;

    const para2 = `The total amount of arrears as detailed in the table below is MUR ${arrearsAmount.toFixed(2)}.`;
    const para2Lines = doc.splitTextToSize(para2, rightMargin - leftMargin);
    para2Lines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 8;

    const tableStartY = yPos;
    const tableHeight = 20;
    const tableWidth = rightMargin - leftMargin;

    doc.rect(leftMargin, tableStartY, tableWidth, tableHeight);

    const col1Width = 65;
    const col2Width = 60;
    const col3Width = tableWidth - col1Width - col2Width;

    const col1X = leftMargin;
    const col2X = leftMargin + col1Width;
    const col3X = leftMargin + col1Width + col2Width;

    doc.line(col2X, tableStartY, col2X, tableStartY + tableHeight);
    doc.line(col3X, tableStartY, col3X, tableStartY + tableHeight);

    doc.setFont('times', 'bold');
    doc.setFontSize(10);
    doc.text('Cover Period', col1X + 3, tableStartY + 7);
    doc.text('Policy Number', col2X + 3, tableStartY + 7);
    doc.text('Amount in Arrears (MUR)', col3X + 3, tableStartY + 7);

    doc.line(leftMargin, tableStartY + 10, rightMargin, tableStartY + 10);

    doc.setFont('times', 'normal');
    doc.setFontSize(10);
    const coverPeriod = polFromDt && polToDt ? `${polFromDt}-${polToDt}` : '';
    doc.text(coverPeriod, col1X + 3, tableStartY + 16);
    doc.text(policyNo, col2X + 3, tableStartY + 16);
    doc.text(arrearsAmount.toFixed(2), col3X + 3, tableStartY + 16);

    yPos = tableStartY + tableHeight + 8;

    doc.setFont('times', 'normal');
    doc.setFontSize(11);
    const bankingPara = 'We invite you to settle the outstanding amount through credit transfer to any of the following bank accounts:';
    const bankingParaLines = doc.splitTextToSize(bankingPara, rightMargin - leftMargin);
    bankingParaLines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 8;

    const bankTableStartY = yPos;
    const bankTableHeight = 38;

    doc.rect(leftMargin, bankTableStartY, tableWidth, bankTableHeight);

    const bankCol1Width = 120;
    const bankCol2Width = tableWidth - bankCol1Width;
    const bankCol1X = leftMargin;
    const bankCol2X = leftMargin + bankCol1Width;

    doc.line(bankCol2X, bankTableStartY, bankCol2X, bankTableStartY + bankTableHeight);

    doc.setFont('times', 'bold');
    doc.setFontSize(10);
    doc.text('Banking Institution', bankCol1X + 3, bankTableStartY + 8);
    doc.text('Account Number', bankCol2X + 3, bankTableStartY + 8);

    doc.line(leftMargin, bankTableStartY + 12, rightMargin, bankTableStartY + 12);

    doc.setFont('times', 'normal');
    doc.setFontSize(10);
    const bankingData = [
      ['Mauritius Commercial Bank (MCB)', '000444155708'],
      ['State Bank of Mauritius (SBM)', '61030100056840'],
      ['Absa Bank', '142005212'],
      ['MauBank', '143100007063']
    ];

    const availableDataSpace = bankTableHeight - 12;
    const equalRowHeight = availableDataSpace / 4;

    let bankRowY = bankTableStartY + 12 + (equalRowHeight / 2) + 2;

    bankingData.forEach((row, index) => {
      doc.text(row[0], bankCol1X + 3, bankRowY);
      doc.text(row[1], bankCol2X + 3, bankRowY);

      if (index < bankingData.length - 1) {
        const separatorY = bankTableStartY + 12 + ((index + 1) * equalRowHeight);
        doc.line(leftMargin, separatorY, rightMargin, separatorY);
      }

      bankRowY += equalRowHeight;
    });

    yPos = bankTableStartY + bankTableHeight + 8;

    doc.setFont('times', 'normal');
    doc.setFontSize(11);

    const policyReminder = `To facilitate the identification of your payment, please ensure that the Policy Number ${policyNo} is quoted in the description/remarks section when conducting the transfer.`;
    const policyReminderLines = doc.splitTextToSize(policyReminder, rightMargin - leftMargin);
    policyReminderLines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 6;

    const deadlinePara = `Maintaining timely payments ensures uninterrupted coverage and access to your benefits. Please arrange to settle the overdue amount by ${dueDate} to avoid any disruption to your Insurance Policy.`;
    const deadlineParaLines = doc.splitTextToSize(deadlinePara, rightMargin - leftMargin);
    deadlineParaLines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 6;

    const disregardPara = 'Kindly disregard this letter if you have already settled the arrears on your Policy.';
    const disregardParaLines = doc.splitTextToSize(disregardPara, rightMargin - leftMargin);
    disregardParaLines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 6;

    const contactPara = 'Should you have any further query regarding this letter, please contact our Customer Service Team on 6023000 or email us at giarrearsrecovery@nicl.mu. Alternately, you may also liaise with your Insurance Advisor.';
    const contactParaLines = doc.splitTextToSize(contactPara, rightMargin - leftMargin);
    contactParaLines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 6;

    const thanksPara = 'Thank you for your cooperation and understanding on this matter.';
    const thanksParaLines = doc.splitTextToSize(thanksPara, rightMargin - leftMargin);
    thanksParaLines.forEach(line => {
      doc.text(line, leftMargin, yPos);
      yPos += 4;
    });
    yPos += 6;

    doc.setFont('times', 'normal');
    doc.setFontSize(10);
    const computerNotice = 'This is a computer generated document and requires no signature.';
    doc.text(computerNotice, leftMargin, yPos);

    const noticeWidth = doc.getTextWidth(computerNotice);
    doc.line(leftMargin, yPos + 1, leftMargin + noticeWidth, yPos + 1);

    return doc;
  };







  const sendEmail = async (rowData, pdfBlob) => {
    if (!emailConfig.serviceId || !emailConfig.templateId || !emailConfig.publicKey) {
      console.error('EmailJS configuration is incomplete:', emailConfig);
      throw new Error('EmailJS configuration is incomplete');
    }

    const policyholderName = `${rowData['Owner 1 Title'] || ''} ${rowData['Owner 1 First Name'] || ''} ${rowData['Owner 1 Surname'] || ''}`.trim();
    const emailId = rowData['EMAIL_ID'] || '';
    const policyNo = rowData['Policy No'] || '';

    if (!emailId) {
      console.error('No email address found for policy:', policyNo);
      throw new Error('No email address found');
    }

    // Log policy number to confirm its value
    console.log('Raw policy number:', policyNo);

    // Convert PDF Blob to base64
    let base64PDF;
    try {
      base64PDF = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = () => reject(new Error('Failed to convert PDF to base64'));
        reader.readAsDataURL(pdfBlob);
      });
    } catch (error) {
      console.error('Error converting PDF to base64:', error.message);
      throw error;
    }

    // Calculate sizes
    const base64SizeKB = (base64PDF.length * 3) / 4 / 1024;
    console.log('Base64 PDF attachment size:', base64SizeKB.toFixed(2), 'KB');

    const templateParams = {
      to_email: emailId,
      to_name: policyholderName,
      subject: `Arrear reminder for your policy Number: ${policyNo}`,
      message: `Dear ${policyholderName}

We would like to remind you regarding your arrears for the Policy number ${policyNo}. 
Please find the arrears notice attached.

Regards
NIC Team
+230 6023000`,
      policy_number: policyNo,
      attachment: base64PDF,
      attachment_name: `${policyNo}_${policyholderName.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`,
    };

    // Calculate size of templateParams (excluding attachment)
    const paramsWithoutAttachment = { ...templateParams, attachment: undefined, attachment_name: undefined };
    const paramsSizeKB = (new TextEncoder().encode(JSON.stringify(paramsWithoutAttachment)).length) / 1024;
    console.log('templateParams (without attachment) size:', paramsSizeKB.toFixed(2), 'KB');

    // Validate sizes
    if (base64SizeKB > 500) {
      console.error('Attachment size exceeds EmailJS 500KB limit:', base64SizeKB.toFixed(2), 'KB');
      throw new Error('Attachment size exceeds EmailJS 500KB limit');
    }

    if (paramsSizeKB > 50) {
      console.error('templateParams (without attachment) exceeds EmailJS 50KB limit:', paramsSizeKB.toFixed(2), 'KB');
      Object.keys(paramsWithoutAttachment).forEach((key) => {
        const valueSizeKB = (new TextEncoder().encode(JSON.stringify(paramsWithoutAttachment[key])).length) / 1024;
        console.log(`Field ${key} size: ${valueSizeKB.toFixed(2)} KB`);
      });
      throw new Error('templateParams exceeds EmailJS 50KB variables limit');
    }

    try {
      console.log('Sending email with attachment to:', emailId);
      console.log('EmailJS config:', {
        serviceId: emailConfig.serviceId,
        templateId: emailConfig.templateId,
        publicKey: emailConfig.publicKey,
      });
      const response = await emailjs.send(
        emailConfig.serviceId,
        emailConfig.templateId,
        templateParams
      );
      console.log('Email sent successfully:', response);
      return response;
    } catch (error) {
      console.error('EmailJS error:', error);
      throw error;
    }
  };

  const downloadPDF = (result) => {
    const link = document.createElement('a');
    link.href = result.url;
    link.download = result.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(result.url); // Clean up URL
  };

  // Process and discard - immediate download without storing
  const downloadPDFImmediate = (pdf, rowData) => {
    const policyNo = rowData['POL_NO'] || rowData['Policy No'] || 'policy';
    const name = rowData['POLICYHOLDER_NAME'] ||
      `${rowData['Owner 1 Title'] || ''} ${rowData['Owner 1 First Name'] || ''} ${rowData['Owner 1 Surname'] || ''}`.trim();

    const pdfBlob = pdf.output('blob');
    const pdfUrl = URL.createObjectURL(pdfBlob);
    const filename = `${policyNo}_${name.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`;

    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up immediately
    URL.revokeObjectURL(pdfUrl);
  };

  const downloadAllPDFs = () => {
    const successfulResults = results.filter(r => r.status === 'success');

    if (successfulResults.length === 0) {
      setError('No PDFs available to download');
      return;
    }

    successfulResults.forEach((result, index) => {
      setTimeout(() => {
        downloadPDF(result);
      }, index * 200);
    });
  };

  // Generate PDFs using Python scripts
  const generatePDFsWithPython = async () => {
    try {
      // Create FormData with Excel file
      const formData = new FormData();

      // Convert data back to Excel format
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
      const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      const excelBlob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

      // Generate output folder name based on file
      const outputFolder = getOutputFolderName(file.name);
      console.log(`[DEBUG] File name: ${file.name}`);
      console.log(`[DEBUG] Output folder: ${outputFolder}`);
      console.log(`[DEBUG] Previous month: ${getPreviousMonthFolder()}`);

      formData.append('excelFile', excelBlob, 'Generic_Template.xlsx');
      formData.append('template', selectedTemplate);
      formData.append('outputFolder', outputFolder);

      console.log(`[DEBUG] FormData contents:`);
      console.log(`[DEBUG] - template: ${selectedTemplate}`);
      console.log(`[DEBUG] - outputFolder: ${outputFolder}`);
      console.log(`Calling Python script: ${selectedTemplate}`);
      setPythonProgress(10);

      // Note: No timeout set - allows up to 6 hours for large PDF generation jobs
      // Server is configured with 6-hour timeout to match Python script timeout
      const response = await fetch(`${API_BASE}/api/generate-pdfs`, {
        method: 'POST',
        body: formData
      });

      setPythonProgress(50);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Server error response:', errorData);
        throw new Error(errorData.message || 'Python PDF generation failed');
      }

      const result = await response.json();
      console.log('Python generation result:', result);

      setPythonProgress(100);
      setGeneratedPdfPaths(result.files);

      return result.files;
    } catch (error) {
      console.error('Python PDF generation error:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        selectedTemplate
      });
      throw error;
    }
  };

  // Enhanced download with progress
  const downloadWithProgress = async (filename) => {
    try {
      // Get file info first
      const infoResponse = await fetch(`${API_BASE}/api/pdf-info/${filename}`);
      if (infoResponse.ok) {
        const fileInfo = await infoResponse.json();
        if (fileInfo.success) {
          setDownloadInfo({
            filename: filename,
            size: fileInfo.size,
            estimatedTime: fileInfo.estimatedDownloadTime
          });
          setShowDownloadProgress(true);
          return;
        }
      }
      // Fallback to direct download if file info fails
      await downloadPDFFromServer(filename);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  };

  // Download PDF from server
  const downloadPDFFromServer = async (filename) => {
    try {
      const response = await fetch(`${API_BASE}/api/pdf/${filename}`);
      if (!response.ok) throw new Error('Failed to download PDF');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      throw error;
    }
  };

  // Process single item with immediate cleanup
  const processItem = async (row, index) => {
    const policyNo = row['Policy No'] || `policy_${index}`;
    const name = row['POLICYHOLDER_NAME'] ||
      `${row['Owner 1 Title'] || ''} ${row['Owner 1 First Name'] || ''} ${row['Owner 1 Surname'] || ''}`.trim();

    try {
      const pdf = await generatePDF(row);

      if (sendEmails) {
        const pdfBlob = pdf.output('blob');
        await sendEmail(row, pdfBlob);
        return {
          policyNo,
          name,
          email: row['EMAIL_ID'] || '',
          status: 'sent',
          type: 'email'
        };
      } else if (autoDownload) {
        // Immediate download and cleanup
        downloadPDFImmediate(pdf, row);
        return {
          policyNo,
          name,
          status: 'downloaded',
          type: 'download'
        };
      }

      return {
        policyNo,
        name,
        status: 'generated',
        type: 'generated'
      };
    } catch (error) {
      console.error(`Error processing ${policyNo}:`, error);
      return {
        policyNo,
        name,
        error: error.message,
        status: 'failed',
        type: 'error'
      };
    }
  };

  // Process batch with concurrency control
  const processBatch = async (batch, batchIndex) => {
    console.log(`Processing batch ${batchIndex + 1}/${totalBatches} (${batch.length} items)`);

    const batchResults = [];

    // Process items in the batch with concurrency limit
    for (let i = 0; i < batch.length; i += concurrentLimit) {
      const chunk = batch.slice(i, i + concurrentLimit);
      const chunkPromises = chunk.map((row, chunkIndex) =>
        processItem(row, (batchIndex * batchSize) + i + chunkIndex)
      );

      try {
        const chunkResults = await Promise.allSettled(chunkPromises);

        chunkResults.forEach((result, chunkIndex) => {
          if (result.status === 'fulfilled') {
            batchResults.push(result.value);
            if (result.value.status === 'sent' || result.value.status === 'downloaded' || result.value.status === 'generated') {
              setProcessedCount(prev => prev + 1);
            } else {
              setFailedCount(prev => prev + 1);
            }
          } else {
            console.error('Promise rejected:', result.reason);
            batchResults.push({
              policyNo: `batch_${batchIndex}_item_${i + chunkIndex}`,
              name: 'Unknown',
              error: result.reason?.message || 'Unknown error',
              status: 'failed',
              type: 'error'
            });
            setFailedCount(prev => prev + 1);
          }
        });

        // Update progress
        const totalProcessed = (batchIndex * batchSize) + i + chunk.length;
        setProgress((totalProcessed / data.length) * 100);

        // Small delay between chunks to prevent overwhelming
        if (i + concurrentLimit < batch.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      } catch (error) {
        console.error('Chunk processing error:', error);
      }
    }

    return batchResults;
  };

  // Function to combine PDFs from selected folder
  const handleCombinePDFs = async () => {
    if (!selectedFolder) {
      setError('Please select a folder to combine PDFs from.');
      return;
    }

    if (!combinedPdfName.trim()) {
      setError('Please enter a name for the combined PDF file.');
      return;
    }

    setProcessing(true);
    setProgress(0);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/combine-pdfs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          folderName: selectedFolder,
          outputName: combinedPdfName.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to combine PDFs');
      }

      const result = await response.json();
      setProgress(100);

      // Download the combined PDF
      console.log('[DEBUG] Combined PDF result:', result);
      const downloadResponse = await fetch(`${API_BASE}/api/pdf/${result.filename}`);
      if (downloadResponse.ok) {
        const blob = await downloadResponse.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        // Show success message with folder location
        console.log(`✅ Combined PDF saved to: ${result.folderPath}/${result.filename}`);
      } else {
        throw new Error('Failed to download combined PDF');
      }

      console.log('PDFs combined successfully:', result);
    } catch (error) {
      console.error('Error combining PDFs:', error);
      setError(`Failed to combine PDFs: ${error.message}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleGeneratePDFs = async () => {
    if (!data.length) {
      setError('No data to process. Please upload an Excel file first.');
      return;
    }

    if (sendEmails && (!emailConfig.serviceId || !emailConfig.templateId || !emailConfig.publicKey)) {
      setError('Please configure EmailJS settings before sending emails.');
      return;
    }

    // Validate that we have the correct template for the file
    const expectedTemplate = getTemplateForFile(file.name);
    if (!expectedTemplate) {
      setError(`Unsupported file format: "${file.name}". Please use one of the supported formats: output_sph.xlsx, output_JPH.xlsx, output_company_sph.xlsx, output_sph_MED.xlsx, or output_JPH_MED.xlsx`);
      return;
    }

    const templateExists = availableTemplates.find(t => t.filename === expectedTemplate);
    if (!templateExists) {
      setError(`Required template "${expectedTemplate}" not found for file "${file.name}". Please ensure the correct Python template files are available.`);
      return;
    }

    if (selectedTemplate !== expectedTemplate) {
      // Automatically correct the template selection
      setSelectedTemplate(expectedTemplate);
      console.log(`Auto-corrected template to: ${expectedTemplate}`);
    }

    // Reset state completely
    setProcessing(true);
    setProgress(0);
    setResults([]);
    setEmailResults([]);
    setEmailProgress(0);
    setProcessedCount(0);
    setFailedCount(0);
    setCurrentBatch(0);
    setPythonProgress(0);
    setGeneratedPdfPaths([]);
    setError('');

    let progressInterval;

    try {
      // Python-based PDF generation (only method available)
      console.log('Starting Python PDF generation...');
      setProgress(5);

      // Start progress simulation based on data size
      const totalRows = data.length;
      const estimatedTimeMs = totalRows * 2000; // Estimate 2 seconds per PDF
      progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + (90 / (estimatedTimeMs / 1000)); // Progress to 90% over estimated time
          return Math.min(newProgress, 90); // Cap at 90% until actual completion
        });
      }, 1000);

      const generatedFiles = await generatePDFsWithPython();
      clearInterval(progressInterval);
      setProgress(95);

      // Update processed count with actual generated files
      setProcessedCount(generatedFiles.length);

      console.log(`Python generated ${generatedFiles.length} PDFs`);

      if (sendEmails) {
        // Process emails via Brevo
        console.log('Starting Brevo email processing...');
        setProgress(40);

        try {
          // Function to sanitize filename consistently with Python
          const sanitizeFilename = (text) => {
            if (!text) return '';
            // Ensure text is a string
            const textStr = String(text);
            try {
              return textStr
                .normalize('NFD') // Decompose Unicode
                .replace(/[\u0300-\u036f]/g, '') // Remove combining characters (accents)
                .replace(/[^\w\s-]/g, '_') // Replace special characters with underscores (including /)
                .replace(/\s+/g, '_') // Replace spaces with underscores
                .replace(/_+/g, '_') // Remove multiple underscores
                .replace(/^_|_$/g, ''); // Remove leading/trailing underscores
            } catch (e) {
              // Fallback for browsers that don't support normalize
              return textStr
                .replace(/[^\w\s-]/g, '_') // Replace special characters with underscores (including /)
                .replace(/\s+/g, '_') // Replace spaces with underscores
                .replace(/_+/g, '_') // Remove multiple underscores
                .replace(/^_|_$/g, ''); // Remove leading/trailing underscores
            }
          };

          // Prepare email data for Brevo
          const emailData = data.slice(0, generatedFiles.length).map((row, i) => {
            const name = `${row['Owner 1 Title'] || ''} ${row['Owner 1 First Name'] || ''} ${row['Owner 1 Surname'] || ''}`.trim() || 'Unknown';
            const policyNo = row['Policy No'] || `policy_${i}`;

            // Create filename using same logic as Python scripts
            const safeName = sanitizeFilename(name);
            const safePolicy = sanitizeFilename(policyNo);
            const expectedFilename = `${safePolicy}_${safeName}.pdf`;

            return {
              email: row['EMAIL_ID'] || '',
              name: name,
              policy_no: policyNo,
              pdf_filename: expectedFilename
            };
          }).filter(item => item.email && item.pdf_filename);

          console.log(`[DEBUG] Sending ${emailData.length} emails via Brevo`);

          const emailResponse = await fetch(`${API_BASE}/api/send-emails-brevo`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
              emailData: emailData,
              folderName: getOutputFolderName(file.name)
            }),
          });

          if (!emailResponse.ok) {
            const errorData = await emailResponse.json();
            throw new Error(errorData.message || 'Failed to send emails via Brevo');
          }

          const emailResult = await emailResponse.json();
          console.log('Brevo email result:', emailResult);

          // Process results
          const emailResults = [];
          if (emailResult.results && emailResult.results.results) {
            emailResult.results.results.forEach((result, i) => {
              emailResults.push({
                policyNo: emailData[i]?.policy_no || `policy_${i}`,
                name: emailData[i]?.name || 'Unknown',
                email: result.email,
                status: result.status,
                messageId: result.message_id,
                error: result.error,
                type: 'email'
              });

              if (result.status === 'sent') {
                setProcessedCount(prev => prev + 1);
              } else {
                setFailedCount(prev => prev + 1);
              }
            });
          }

          setEmailResults(emailResults);
          setProgress(100);

        } catch (emailError) {
          console.error('Brevo email processing failed:', emailError);
          setError(`Email sending failed: ${emailError.message}`);
          // Use data.length as fallback if emailData is not defined
          const emailCount = typeof emailData !== 'undefined' ? emailData.length : data.length;
          setFailedCount(prev => prev + emailCount);
        }

      } else if (autoDownload) {
        // Auto-download all generated PDFs
        console.log('Starting auto-download...');
        for (let i = 0; i < generatedFiles.length; i++) {
          try {
            await downloadPDFFromServer(generatedFiles[i].filename);
            setProcessedCount(prev => prev + 1);
            setProgress(30 + ((i + 1) / generatedFiles.length) * 70);

            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 300));
          } catch (downloadError) {
            console.error('Download failed:', downloadError);
            setFailedCount(prev => prev + 1);
          }
        }
      }

      // Update results
      const pdfResults = generatedFiles.map((file, index) => ({
        policyNo: data[index]?.['Policy No'] || `policy_${index}`,
        name: `${data[index]?.['Owner 1 Title'] || ''} ${data[index]?.['Owner 1 First Name'] || ''} ${data[index]?.['Owner 1 Surname'] || ''}`.trim() || 'Unknown',
        filename: file.filename,
        size: file.size,
        status: 'generated',
        type: 'python_pdf'
      }));

      setResults(pdfResults);
      setProgress(100);



      console.log(`Processing complete. Processed: ${processedCount}, Failed: ${failedCount}`);

    } catch (error) {
      console.error('Processing error:', error);
      setError(`Processing failed: ${error.message}`);
      // Clear any running progress intervals
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', width: '100vw', margin: 0, padding: 0 }}>
      {/* Full-width header */}
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        color: 'white',
        padding: '32px',
        width: '100%',
        boxSizing: 'border-box',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', margin: 0, letterSpacing: '-0.025em' }}>
              NIC Life - Arrears Management
            </h1>
            <p style={{ color: '#cbd5e1', marginTop: '12px', margin: 0, fontSize: '1.125rem', fontWeight: '500' }}>
              Arrears Letter Generation & Email Distribution Platform
            </p>
          </div>
          <div>
            <img src={sicomLogo} alt="NIC Logo" style={{ height: '130px', width: 'auto', filter: 'brightness(1.1)', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', borderRadius: '8px' }} />
          </div>
        </div>
      </div>

      {/* Main content area - Full width */}
      <div style={{
        width: '100%',
        minHeight: 'calc(100vh - 140px)',
        padding: '40px',
        background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
      }}>

        {/* Authentication Check */}
        {!isAuthenticated ? (
          <AuthScreen onAuthenticated={handleAuthenticated} />
        ) : (
          <>
            {/* User Info Bar */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6 flex justify-between items-center">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-3">
                  <span className="text-white font-bold text-sm">
                    {userEmail.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">Welcome, {userEmail}</p>
                  <p className="text-xs text-gray-500">NIC PDF Generator - Authenticated Session</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center px-4 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut size={16} className="mr-2" />
                Logout
              </button>
            </div>

            {/* Tab Navigation */}
            <TabNavigation
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            {/* Tab Content */}
            {activeTab === 'combine' && (
              <>
                {/* 3-Step Workflow Header */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-sm border border-blue-200 p-6 mb-8">
                  <h2 className="text-2xl font-bold mb-4 text-gray-800 text-center">PDF Generation Workflow</h2>
                  <div className="flex flex-col md:flex-row items-center justify-center space-y-4 md:space-y-0 md:space-x-8">
                    <div className="flex items-center text-center">
                      <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">1</div>
                      <div>
                        <p className="font-semibold text-gray-800">Upload Excel</p>
                        <p className="text-sm text-gray-600">Select your data file</p>
                      </div>
                    </div>
                    <div className="hidden md:block text-gray-400">→</div>
                    <div className="flex items-center text-center">
                      <div className="w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center font-bold mr-3">2</div>
                      <div>
                        <p className="font-semibold text-gray-800">Generate PDFs</p>
                        <p className="text-sm text-gray-600">Create individual letters</p>
                      </div>
                    </div>
                    <div className="hidden md:block text-gray-400">→</div>
                    <div className="flex items-center text-center">
                      <div className="w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-3">3</div>
                      <div>
                        <p className="font-semibold text-gray-800">Combine & Download</p>
                        <p className="text-sm text-gray-600">Merge into single file</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step 1: Upload Excel File */}
                <div className={`bg-white rounded-xl shadow-sm border p-8 mb-8 ${!file ? 'border-blue-300 bg-blue-50' : 'border-gray-200'}`}>
                  <div className="flex items-center mb-6">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mr-3 ${!file ? 'bg-blue-600 text-white' : 'bg-green-600 text-white'}`}>
                      {!file ? '1' : '✓'}
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800">Upload Excel File</h2>
                    {file && <span className="ml-3 text-sm text-green-600 font-medium">✓ Completed</span>}
                  </div>

                  {!file && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
                      <h2 className="text-2xl font-bold mb-6 flex items-center text-gray-800">
                        <FileText className="mr-3 text-blue-600" size={28} />
                        Upload Excel File
                      </h2>
                      <div className="border-2 border-dashed border-blue-300 rounded-xl p-12 text-center bg-blue-50 hover:bg-blue-100 transition-colors">
                        <input
                          type="file"
                          accept=".xlsx,.xls"
                          onChange={handleFileUpload}
                          className="hidden"
                          id="file-upload"
                          aria-label="Upload Excel file"
                        />
                        <label htmlFor="file-upload" className="cursor-pointer">
                          <Upload className="mx-auto h-16 w-16 text-blue-500 mb-6" />
                          <p className="text-lg font-medium text-gray-700 mb-3">Click to upload Excel file</p>
                          <p className="text-sm text-gray-500">Drag and drop your Excel file here or click to browse</p>
                        </label>
                      </div>

                      {file && (
                        <div className="mt-6 p-5 bg-green-50 border border-green-200 rounded-xl">
                          <p className="text-green-800 flex items-center text-base font-medium">
                            <CheckCircle className="mr-3 text-green-600" size={20} />
                            File: {file.name} ({data.length} records loaded)
                          </p>
                        </div>
                      )}

                      {error && (
                        <div className="mt-6 p-5 bg-red-50 border border-red-200 rounded-xl">
                          <p className="text-red-800 flex items-center text-base font-medium">
                            <AlertCircle className="mr-3 text-red-600" size={20} />
                            {error}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                </div>

                {/* Step 2: Generate PDFs */}
                {data.length > 0 && (
                  <div className={`bg-white rounded-xl shadow-sm border p-8 mb-8 ${results.length === 0 && data.length > 0 ? 'border-green-300 bg-green-50' : 'border-gray-200'}`}>
                    <div className="flex items-center mb-6">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mr-3 ${results.length === 0 ? 'bg-green-600 text-white' : 'bg-green-600 text-white'}`}>
                        {results.length === 0 ? '2' : '✓'}
                      </div>
                      <h2 className="text-2xl font-bold text-gray-800">Generate PDFs</h2>
                      {results.length > 0 && <span className="ml-3 text-sm text-green-600 font-medium">✓ Completed</span>}
                    </div>

                    {/* Two-Column Layout */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">

                      {/* Left Column: Template Information */}
                      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
                        <h3 className="text-lg font-bold mb-4 text-gray-800 flex items-center">
                          <FileText className="mr-2 text-blue-600" size={20} />
                          PDF Template
                        </h3>

                        {/* Template Display */}
                        <div className={`w-full px-4 py-3 text-sm border rounded-lg font-medium mb-3 ${file && !getTemplateForFile(file.name)
                          ? 'border-red-200 bg-red-50 text-red-700'
                          : 'border-blue-200 bg-white text-gray-700'
                          }`}>
                          {file ? (() => {
                            const autoTemplate = getTemplateForFile(file.name);
                            if (autoTemplate) {
                              const templateInfo = availableTemplates.find(t => t.filename === autoTemplate);
                              return templateInfo ? templateInfo.displayName : autoTemplate;
                            }
                            return 'ERROR: Unsupported file format';
                          })() : 'Upload file to see template'}
                        </div>

                        {/* Template Validation */}
                        {file && (() => {
                          const autoTemplate = getTemplateForFile(file.name);
                          if (autoTemplate) {
                            const templateExists = availableTemplates.find(t => t.filename === autoTemplate);
                            return (
                              <div className={`p-3 text-xs rounded-lg ${templateExists
                                ? 'bg-green-100 text-green-700 border border-green-200'
                                : 'bg-red-100 text-red-700 border border-red-200'
                                }`}>
                                {templateExists
                                  ? `✓ Auto-selected for "${file.name}"`
                                  : `❌ Template not found`
                                }
                              </div>
                            );
                          } else {
                            return (
                              <div className="p-3 text-xs rounded-lg bg-red-100 text-red-700 border border-red-200">
                                ❌ Unsupported file format
                              </div>
                            );
                          }
                        })()}
                      </div>

                      {/* Right Column: Processing Options */}
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-6">
                        <h3 className="text-lg font-bold mb-4 text-gray-800 flex items-center">
                          <Settings className="mr-2 text-green-600" size={20} />
                          Processing Options
                        </h3>

                        {/* Time & Folder Info */}
                        <div className="space-y-3 mb-4">
                          <div className="flex items-center text-sm text-gray-700">
                            <span className="text-green-600 mr-2">⏱️</span>
                            <span className="font-medium">Time:</span>
                            <span className="ml-1">~1 minute</span>
                          </div>
                          {file && (
                            <div className="flex items-center text-sm text-gray-700">
                              <span className="text-blue-600 mr-2">📁</span>
                              <span className="font-medium">Folder:</span>
                              <span className="ml-1 truncate">{getOutputFolderName(file.name)}/</span>
                            </div>
                          )}
                        </div>

                        {/* Download/Email Options */}
                        <div className="space-y-3">
                          <label className="flex items-center cursor-pointer p-3 bg-white rounded-lg border border-blue-200 hover:bg-blue-50 transition-colors">
                            <input
                              type="checkbox"
                              checked={autoDownload}
                              onChange={(e) => setAutoDownload(e.target.checked)}
                              disabled={sendEmails}
                              className="mr-3 w-4 h-4 text-blue-600"
                            />
                            <Download className="mr-2 text-blue-600" size={16} />
                            <span className="text-sm font-medium text-gray-800">Auto-download PDFs</span>
                          </label>

                          <label className="flex items-center cursor-pointer p-3 bg-white rounded-lg border border-green-200 hover:bg-green-50 transition-colors">
                            <input
                              type="checkbox"
                              checked={sendEmails}
                              onChange={(e) => {
                                setSendEmails(e.target.checked);
                                if (e.target.checked) setAutoDownload(false);
                              }}
                              className="mr-3 w-4 h-4 text-green-600"
                            />
                            <Mail className="mr-2 text-green-600" size={16} />
                            <span className="text-sm font-medium text-gray-800">Send via email</span>
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* Generate PDFs Button */}
                    <div className="flex justify-center mb-6">
                      <button
                        onClick={handleGeneratePDFs}
                        disabled={processing || !file || !getTemplateForFile(file?.name)}
                        className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-4 rounded-xl font-semibold text-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none"
                      >
                        {processing ? (
                          <>
                            <Loader className="animate-spin mr-3" size={24} />
                            Generating PDFs...
                          </>
                        ) : (
                          <>
                            <FileText className="mr-3" size={24} />
                            Generate {data.length} PDFs
                          </>
                        )}
                      </button>
                    </div>

                    {/* Progress Bar */}
                    {processing && (
                      <div className="mb-6">
                        <div className="bg-white rounded-lg p-4 border">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-gray-700">Generation Progress</span>
                            <span className="text-sm text-gray-600">{Math.round(progress)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div
                              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>
                          <div className="mt-2 text-xs text-gray-600">
                            {processedCount > 0 && (
                              <span>Processed: {processedCount}/{data.length} | Failed: {failedCount}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}



                    <div className="flex gap-6 mb-8">
                      <button
                        onClick={handleGeneratePDFs}
                        disabled={processing}
                        className="flex-1 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-4 rounded-xl font-semibold text-lg flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none"
                        aria-label={sendEmails ? 'Generate and email PDFs' : 'Generate all PDFs'}
                      >
                        {processing ? (
                          <>
                            <Loader className="animate-spin mr-3" size={24} />
                            Processing...
                          </>
                        ) : (
                          <>
                            {sendEmails ? <Mail className="mr-3" size={24} /> : <FileText className="mr-3" size={24} />}
                            {sendEmails ? 'Generate & Email' : 'Generate All PDFs'} ({data.length})
                          </>
                        )}
                      </button>

                      {results.length > 0 && !processing && !sendEmails && (
                        <button
                          onClick={downloadAllPDFs}
                          className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-8 py-4 rounded-xl font-semibold text-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
                          aria-label="Download all generated PDFs"
                        >
                          <Download className="mr-3" size={24} />
                          Download All
                        </button>
                      )}
                    </div>

                    {processing && (
                      <div className="mb-4">
                        <div className="bg-white rounded-lg p-4 border">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-gray-700">Overall Progress</span>
                            <span className="text-sm text-gray-600">{Math.round(progress)}%</span>
                          </div>
                          <div className="bg-gray-200 rounded-full h-3 mb-3">
                            <div
                              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>

                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <div className="text-gray-600">Batch Progress</div>
                              <div className="font-medium">{currentBatch} / {totalBatches}</div>
                            </div>
                            <div>
                              <div className="text-gray-600">Items Processed</div>
                              <div className="font-medium">{processedCount} / {data.length}</div>
                            </div>
                          </div>

                          {failedCount > 0 && (
                            <div className="mt-2 text-sm">
                              <span className="text-red-600">Failed: {failedCount}</span>
                            </div>
                          )}

                          <div className="mt-3">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs text-gray-600">Python PDF Generation</span>
                              <span className="text-xs text-gray-600">{Math.round(pythonProgress)}%</span>
                            </div>
                            <div className="bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${pythonProgress}%` }}
                              ></div>
                            </div>
                          </div>

                          <div className="mt-2 text-xs text-gray-500">
                            Using ${selectedTemplate.replace('.py', '')} template
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Step 3: Combine PDFs */}
                <div className={`bg-white rounded-xl shadow-sm border p-8 mb-8 ${results.length > 0 ? 'border-purple-300 bg-purple-50' : 'border-gray-200'}`}>
                  <div className="flex items-center mb-6">
                    <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-3">3</div>
                    <h2 className="text-2xl font-bold text-gray-800">Combine PDFs</h2>
                    {results.length > 0 && <span className="ml-3 text-sm text-purple-600 font-medium">Ready to combine</span>}
                  </div>

                  {/* Folder Selection */}
                  <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200 p-6 mb-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-bold text-gray-800">Select PDF Folder</h3>
                      <button
                        onClick={() => {
                          const fetchFolders = async () => {
                            try {
                              console.log('[DEBUG] Refreshing folders...');
                              const response = await fetch(`${API_BASE}/api/folders`, {
                                headers: {
                                  'Authorization': `Bearer ${authToken}`
                                }
                              });
                              const data = await response.json();
                              console.log('[DEBUG] Folders response:', data);
                              if (data.success) {
                                console.log('[DEBUG] Available folders:', data.folders);
                                setAvailableFolders(data.folders);
                              }
                            } catch (error) {
                              console.error('Failed to refresh folders:', error);
                            }
                          };
                          fetchFolders();
                        }}
                        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        🔄 Refresh
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-600 mb-3">
                          Available Folders ({availableFolders.length} found)
                        </label>
                        <select
                          value={selectedFolder}
                          onChange={(e) => setSelectedFolder(e.target.value)}
                          className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg bg-white text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-green-500"
                          disabled={processing}
                        >
                          <option value="">
                            {availableFolders.length === 0 ? 'No folders found...' : 'Select a folder...'}
                          </option>
                          {availableFolders.map(folder => (
                            <option key={folder.name} value={folder.name}>
                              {folder.name} ({folder.pdfCount} PDFs)
                            </option>
                          ))}
                        </select>

                        {availableFolders.length === 0 && (
                          <p className="text-xs text-gray-500 mt-2">
                            💡 Generate some PDFs first, then refresh to see available folders
                          </p>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-600 mb-3">Combined PDF Name</label>
                        <input
                          type="text"
                          value={combinedPdfName}
                          onChange={(e) => setCombinedPdfName(e.target.value)}
                          placeholder="Enter filename (without .pdf)"
                          className="w-full px-4 py-3 text-base border border-gray-200 rounded-lg bg-white text-gray-700 font-medium focus:outline-none focus:ring-2 focus:ring-green-500"
                          disabled={processing}
                        />
                      </div>
                    </div>

                    {selectedFolder && (
                      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm text-blue-700">
                          📁 Selected: <span className="font-medium">{selectedFolder}</span>
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Combine Button */}
                  <div className="flex justify-center mb-6">
                    <button
                      onClick={handleCombinePDFs}
                      disabled={processing || !selectedFolder || !combinedPdfName.trim()}
                      className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-gray-400 disabled:to-gray-500 text-white px-8 py-4 rounded-xl font-semibold text-lg flex items-center shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none"
                    >
                      {processing ? (
                        <>
                          <Loader className="animate-spin mr-3" size={24} />
                          Combining PDFs...
                        </>
                      ) : (
                        <>
                          <Download className="mr-3" size={24} />
                          Combine PDFs
                        </>
                      )}
                    </button>
                  </div>

                  {/* Progress Bar for Combine Mode */}
                  {processing && (
                    <div className="mb-6">
                      <div className="bg-white rounded-lg p-4 border">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium text-gray-700">Combining Progress</span>
                          <span className="text-sm text-gray-600">{Math.round(progress)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className="bg-green-600 h-3 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

              </>
            )}

            {/* Browse & Download Tab */}
            {activeTab === 'browse' && (
              <FileBrowser
                onDownload={downloadWithProgress}
                API_BASE={API_BASE}
              />
            )}

            {/* Download Progress Modal */}
            <DownloadProgress
              isVisible={showDownloadProgress}
              onClose={() => setShowDownloadProgress(false)}
              filename={downloadInfo?.filename}
              fileSize={downloadInfo?.size}
              estimatedTime={downloadInfo?.estimatedTime}
              onConfirm={() => {
                setShowDownloadProgress(false);
                if (downloadInfo?.filename) {
                  downloadPDFFromServer(downloadInfo.filename);
                }
              }}
              onCancel={() => {
                setShowDownloadProgress(false);
                setDownloadInfo(null);
              }}
            />

            {(results.length > 0 || emailResults.length > 0) && activeTab === 'combine' && (
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Processing Results</h3>
                  <div className="text-sm text-gray-600">
                    Success: {processedCount} | Failed: {failedCount}
                  </div>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="bg-green-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-600">{processedCount}</div>
                    <div className="text-sm text-green-700">Processed</div>
                  </div>
                  <div className="bg-red-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-red-600">{failedCount}</div>
                    <div className="text-sm text-red-700">Failed</div>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-600">{data.length}</div>
                    <div className="text-sm text-blue-700">Total</div>
                  </div>
                </div>

                <h3 className="text-lg font-semibold mb-4">Detailed Results</h3>

                {/* PDF Generation Results */}
                {results.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-700 mb-2">PDF Generation ({results.length})</h4>
                    <div className="bg-white rounded border max-h-40 overflow-y-auto">
                      {results.slice(-10).map((result, index) => (
                        <div key={index} className="px-3 py-2 border-b last:border-b-0 flex justify-between items-center">
                          <div className="flex-1">
                            <span className="text-sm font-medium">{result.policyNo}</span>
                            <span className="text-xs text-gray-500 ml-2">{result.name}</span>
                          </div>
                          <div className="flex items-center">
                            {result.status === 'downloaded' && (
                              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Downloaded</span>
                            )}
                            {result.status === 'generated' && (
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Generated</span>
                            )}
                            {result.status === 'failed' && (
                              <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">Failed</span>
                            )}
                          </div>
                        </div>
                      ))}
                      {results.length > 10 && (
                        <div className="px-3 py-2 text-xs text-gray-500 text-center">
                          Showing last 10 of {results.length} results
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Email Results */}
                {emailResults.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-700 mb-2">Email Sending ({emailResults.length})</h4>
                    <div className="bg-white rounded border max-h-40 overflow-y-auto">
                      {emailResults.slice(-10).map((result, index) => (
                        <div key={index} className="px-3 py-2 border-b last:border-b-0 flex justify-between items-center">
                          <div className="flex-1">
                            <span className="text-sm font-medium">{result.policyNo}</span>
                            <span className="text-xs text-gray-500 ml-2">{result.email}</span>
                          </div>
                          <div className="flex items-center">
                            {result.status === 'sent' && (
                              <CheckCircle className="text-green-600 mr-1" size={16} />
                            )}
                            {result.status === 'failed' && (
                              <AlertCircle className="text-red-600 mr-1" size={16} />
                            )}
                            <span className={`text-xs px-2 py-1 rounded ${result.status === 'sent'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                              }`}>
                              {result.status === 'sent' ? 'Sent' : 'Failed'}
                            </span>
                          </div>
                        </div>
                      ))}
                      {emailResults.length > 10 && (
                        <div className="px-3 py-2 text-xs text-gray-500 text-center">
                          Showing last 10 of {emailResults.length} results
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            {showEmailConfig && (
              <div className="bg-gray-50 rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">EmailJS Configuration</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Service ID
                    </label>
                    <input
                      type="text"
                      value={emailConfig.serviceId}
                      onChange={(e) => setEmailConfig(prev => ({ ...prev, serviceId: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="service_xxxxxxx"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Template ID
                    </label>
                    <input
                      type="text"
                      value={emailConfig.templateId}
                      onChange={(e) => setEmailConfig(prev => ({ ...prev, templateId: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="template_xxxxxxx"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Public Key
                    </label>
                    <input
                      type="text"
                      value={emailConfig.publicKey}
                      onChange={(e) => setEmailConfig(prev => ({ ...prev, publicKey: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Your public key"
                    />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default PDFGenerator;