import express from 'express';
import multer from 'multer';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import cors from 'cors';
import { fileURLToPath } from 'url';
import AuthService from './auth_service.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 3001;

// Check if running in Electron
const isElectron = process.versions && process.versions.electron;

// Middleware
app.use(cors());
// Increase payload size limits for large Excel files (50MB)
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// Configure multer for file uploads with size limits
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = './temp_uploads';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, 'Generic_Template.xlsx');
  }
});

const upload = multer({ 
  storage,
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB limit
  }
});

// Ensure output directory exists
const outputDir = './generated_pdfs';
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// API endpoint to generate PDFs using Python
app.post('/api/generate-pdfs', upload.single('excelFile'), (req, res) => {
  // Set timeout to 6 hours (21600000 ms) to match Python script timeout
  req.setTimeout(21600000); // 6 hours in milliseconds
  res.setTimeout(21600000); // 6 hours in milliseconds

  const { template, outputFolder: customOutputFolder } = req.body;
  const inputFile = req.file.path;

  console.log(`[DEBUG] Received template: ${template}`);
  console.log(`[DEBUG] Received outputFolder: ${customOutputFolder}`);
  console.log(`[DEBUG] Input file path: ${inputFile}`);

  // Use custom output folder if provided, otherwise use default
  const outputFolder = customOutputFolder
    ? path.resolve('.', customOutputFolder)
    : path.resolve(outputDir);

  // Create a backup copy in root directory for fallback with validation
  const fallbackFile = path.resolve('.', 'Generic_Template.xlsx');
  try {
    fs.copyFileSync(inputFile, fallbackFile);

    // Verify the file was copied correctly
    const inputStats = fs.statSync(inputFile);
    const fallbackStats = fs.statSync(fallbackFile);

    if (inputStats.size !== fallbackStats.size) {
      throw new Error(`File size mismatch: input=${inputStats.size}, fallback=${fallbackStats.size}`);
    }

    console.log(`[DEBUG] Created fallback file: ${fallbackFile} (${fallbackStats.size} bytes)`);

    // Also create a timestamped backup for debugging
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const debugFile = path.resolve('.', `Generic_Template_debug_${timestamp}.xlsx`);
    fs.copyFileSync(fallbackFile, debugFile);
    console.log(`[DEBUG] Created debug file: ${debugFile}`);

  } catch (error) {
    console.error(`[ERROR] Could not create fallback file: ${error.message}`);
    // This is critical - if we can't create the fallback, the process will likely fail
    return res.status(500).json({
      success: false,
      message: 'Failed to process uploaded file',
      error: error.message
    });
  }

  console.log(`Starting PDF generation with template: ${template}`);
  console.log(`Input file: ${inputFile}`);
  console.log(`Output folder: ${outputFolder}`);

  // Clear output directory (with error handling for locked files and folders)
  if (fs.existsSync(outputFolder)) {
    fs.readdirSync(outputFolder).forEach(file => {
      try {
        const filePath = path.join(outputFolder, file);
        const stat = fs.statSync(filePath);

        if (stat.isDirectory()) {
          // Remove directory recursively
          fs.rmSync(filePath, { recursive: true, force: true });
        } else {
          // Remove file
          fs.unlinkSync(filePath);
        }
      } catch (error) {
        if (error.code === 'EBUSY' || error.code === 'ENOENT') {
          console.warn(`Warning: Could not delete ${file} (file may be open in another application)`);
        } else {
          console.error(`Error deleting ${file}:`, error.message);
        }
      }
    });
  }

  // Ensure output directory exists
  if (!fs.existsSync(outputFolder)) {
    fs.mkdirSync(outputFolder, { recursive: true });
    console.log(`Created output directory: ${outputFolder}`);
  }

  // Execute Python script via wrapper
  const pythonArgs = [
    'pdf_generator_wrapper.py',
    '--template', template,
    '--input', inputFile,
    '--output', outputFolder
  ];

  console.log(`[DEBUG] Python command: python ${pythonArgs.join(' ')}`);

  const python = spawn('python', pythonArgs, {
    encoding: 'utf8',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });

  let stdout = '';
  let stderr = '';

  python.stdout.on('data', (data) => {
    stdout += data.toString('utf8');
    console.log(`Python stdout: ${data.toString('utf8')}`);
  });

  python.stderr.on('data', (data) => {
    stderr += data.toString('utf8');
    console.error(`Python stderr: ${data.toString('utf8')}`);
  });

  python.on('close', (code) => {
    console.log(`Python script finished with code: ${code}`);

    // Clean up input file
    fs.unlinkSync(inputFile);

    if (code === 0) {
      // Get list of generated PDF files (including from protected/unprotected subfolders)
      let pdfFiles = [];

      // Check main folder
      if (fs.existsSync(outputFolder)) {
        const mainPdfs = fs.readdirSync(outputFolder)
          .filter(file => file.endsWith('.pdf'))
          .map(file => ({
            filename: file,
            path: path.join(outputFolder, file),
            size: fs.statSync(path.join(outputFolder, file)).size,
            location: 'main'
          }));
        pdfFiles.push(...mainPdfs);

        // Check protected subfolder
        const protectedPath = path.join(outputFolder, 'protected');
        if (fs.existsSync(protectedPath)) {
          const protectedPdfs = fs.readdirSync(protectedPath)
            .filter(file => file.endsWith('.pdf'))
            .map(file => ({
              filename: file,
              path: path.join(protectedPath, file),
              size: fs.statSync(path.join(protectedPath, file)).size,
              location: 'protected'
            }));
          pdfFiles.push(...protectedPdfs);
        }

        // Check unprotected subfolder
        const unprotectedPath = path.join(outputFolder, 'unprotected');
        if (fs.existsSync(unprotectedPath)) {
          const unprotectedPdfs = fs.readdirSync(unprotectedPath)
            .filter(file => file.endsWith('.pdf'))
            .map(file => ({
              filename: file,
              path: path.join(unprotectedPath, file),
              size: fs.statSync(path.join(unprotectedPath, file)).size,
              location: 'unprotected'
            }));
          pdfFiles.push(...unprotectedPdfs);
        }
      }

      // Calculate records processed (unique records, not total files)
      const protectedCount = pdfFiles.filter(f => f.location === 'protected').length;
      const unprotectedCount = pdfFiles.filter(f => f.location === 'unprotected').length;
      const mainCount = pdfFiles.filter(f => f.location === 'main').length;
      
      // Records processed = max of protected/unprotected (since each record generates both)
      const recordsProcessed = Math.max(protectedCount, unprotectedCount, mainCount);
      
      res.json({
        success: true,
        message: `Processed ${recordsProcessed} records successfully (${pdfFiles.length} files generated)`,
        files: pdfFiles,
        recordsProcessed: recordsProcessed,
        filesGenerated: pdfFiles.length,
        breakdown: {
          protected: protectedCount,
          unprotected: unprotectedCount,
          main: mainCount
        },
        stdout,
        stderr
      });
    } else {
      res.status(500).json({
        success: false,
        message: 'Python script execution failed',
        stdout,
        stderr,
        code
      });
    }
  });

  python.on('error', (error) => {
    console.error('Failed to start Python process:', error);
    fs.unlinkSync(inputFile);
    res.status(500).json({
      success: false,
      message: 'Failed to start Python process',
      error: error.message
    });
  });
});

// API endpoint to get PDF file
app.get('/api/pdf/:filename', (req, res) => {
  const filename = req.params.filename;

  // Search for the file in multiple possible locations
  const possiblePaths = [
    path.join(outputDir, filename), // Default location
    path.join('.', filename), // Current directory
  ];

  // Add dynamic folder paths (search for folders matching pattern)
  try {
    const currentDir = fs.readdirSync('.');
    const outputFolders = currentDir.filter(item => {
      return fs.statSync(item).isDirectory() &&
        (item.startsWith('output_') || item.startsWith('default_'));
    });

    outputFolders.forEach(folder => {
      // Check combined folder first (most likely location for downloads)
      possiblePaths.push(path.join('.', folder, 'combined', filename));
      possiblePaths.push(path.join('.', folder, filename));
      // Also check protected and unprotected subfolders
      possiblePaths.push(path.join('.', folder, 'protected', filename));
      possiblePaths.push(path.join('.', folder, 'unprotected', filename));
    });
  } catch (error) {
    console.error('Error scanning for output folders:', error);
  }

  // Try each possible path
  let foundPath = null;
  for (const filePath of possiblePaths) {
    if (fs.existsSync(filePath)) {
      foundPath = filePath;
      break;
    }
  }

  if (foundPath) {
    console.log(`[DEBUG] Found PDF at: ${foundPath}`);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    fs.createReadStream(foundPath).pipe(res);
  } else {
    console.error(`[ERROR] PDF not found: ${filename}`);
    console.error(`[ERROR] Searched ${possiblePaths.length} paths:`);
    possiblePaths.forEach((searchPath, index) => {
      const exists = fs.existsSync(searchPath);
      console.error(`[DEBUG] ${index + 1}. ${exists ? '✓' : '✗'} ${searchPath}`);
    });
    res.status(404).json({
      error: 'File not found',
      filename: filename,
      searchedPaths: possiblePaths.length
    });
  }
});

// API endpoint to get available templates
app.get('/api/templates', (req, res) => {
  try {
    const templateFiles = fs.readdirSync('.')
      .filter(file => file.endsWith('.py') && !file.includes('wrapper') && !file.includes('test'))
      .map(file => ({
        filename: file,
        displayName: file  // Show actual filename
      }));

    res.json({
      success: true,
      templates: templateFiles
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Failed to scan for templates',
      error: error.message
    });
  }
});

// API endpoint to get available PDF folders
app.get('/api/folders', (req, res) => {
  try {
    console.log('[DEBUG] Scanning for PDF folders...');
    const allItems = fs.readdirSync('.');
    console.log('[DEBUG] All items in directory:', allItems.length);

    const folders = allItems
      .filter(item => {
        const isDirectory = fs.statSync(item).isDirectory();
        const matchesPattern = item.startsWith('output_') || item.startsWith('default_');
        console.log(`[DEBUG] ${item}: isDirectory=${isDirectory}, matchesPattern=${matchesPattern}`);
        return isDirectory && matchesPattern;
      })
      .map(folder => {
        let pdfCount = 0;

        try {
          // Check for PDFs directly in the folder
          const directPdfs = fs.readdirSync(folder).filter(file => file.endsWith('.pdf'));
          pdfCount += directPdfs.length;

          // Check for PDFs in protected and unprotected subfolders
          const protectedPath = path.join(folder, 'protected');
          const unprotectedPath = path.join(folder, 'unprotected');

          if (fs.existsSync(protectedPath) && fs.statSync(protectedPath).isDirectory()) {
            const protectedPdfs = fs.readdirSync(protectedPath).filter(file => file.endsWith('.pdf'));
            pdfCount += protectedPdfs.length;
            console.log(`[DEBUG] Folder ${folder}/protected: ${protectedPdfs.length} PDFs`);
          }

          if (fs.existsSync(unprotectedPath) && fs.statSync(unprotectedPath).isDirectory()) {
            const unprotectedPdfs = fs.readdirSync(unprotectedPath).filter(file => file.endsWith('.pdf'));
            pdfCount += unprotectedPdfs.length;
            console.log(`[DEBUG] Folder ${folder}/unprotected: ${unprotectedPdfs.length} PDFs`);
          }

        } catch (error) {
          console.error(`[ERROR] Error scanning folder ${folder}:`, error.message);
        }

        console.log(`[DEBUG] Folder ${folder}: ${pdfCount} total PDFs`);
        return {
          name: folder,
          pdfCount: pdfCount
        };
      })
      .filter(folder => folder.pdfCount > 0); // Only show folders with PDFs

    console.log('[DEBUG] Final folders list:', folders);

    res.json({
      success: true,
      folders: folders
    });
  } catch (error) {
    console.error('[ERROR] Failed to scan folders:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to scan for folders',
      error: error.message
    });
  }
});

// NEW: Enhanced API endpoint for folder-based SMS link generation
app.get('/api/pdf-folders-enhanced', (req, res) => {
  try {
    console.log('[DEBUG] Enhanced folder scanning for SMS link generation...');
    const allItems = fs.readdirSync('.');
    
    // Template detection mapping
    const templateMapping = {
      'output_sph_': { template: 'SPH_Fresh.py', templateType: 'SPH' },
      'output_jph_': { template: 'JPH_Fresh.py', templateType: 'JPH' },
      'output_company_': { template: 'Company_Fresh.py', templateType: 'Company' },
      'output_med_sph_': { template: 'MED_SPH_Fresh_Signature.py', templateType: 'MED_SPH' },
      'output_med_jph_': { template: 'MED_JPH_Fresh_Signature.py', templateType: 'MED_JPH' }
    };

    const folders = allItems
      .filter(item => {
        const isDirectory = fs.statSync(item).isDirectory();
        const matchesPattern = item.startsWith('output_') || item.startsWith('default_');
        return isDirectory && matchesPattern;
      })
      .map(folder => {
        let protectedCount = 0;
        let unprotectedCount = 0;
        let totalPdfCount = 0;

        // Detect template type from folder name
        let detectedTemplate = { template: 'Unknown', templateType: 'Unknown' };
        for (const [prefix, templateInfo] of Object.entries(templateMapping)) {
          if (folder.startsWith(prefix)) {
            detectedTemplate = templateInfo;
            break;
          }
        }

        try {
          // Check protected folder
          const protectedPath = path.join(folder, 'protected');
          if (fs.existsSync(protectedPath) && fs.statSync(protectedPath).isDirectory()) {
            const protectedPdfs = fs.readdirSync(protectedPath).filter(file => file.endsWith('.pdf'));
            protectedCount = protectedPdfs.length;
          }

          // Check unprotected folder
          const unprotectedPath = path.join(folder, 'unprotected');
          if (fs.existsSync(unprotectedPath) && fs.statSync(unprotectedPath).isDirectory()) {
            const unprotectedPdfs = fs.readdirSync(unprotectedPath).filter(file => file.endsWith('.pdf'));
            unprotectedCount = unprotectedPdfs.length;
          }

          // Check for direct PDFs (fallback)
          const directPdfs = fs.readdirSync(folder).filter(file => file.endsWith('.pdf'));
          totalPdfCount = Math.max(protectedCount, unprotectedCount, directPdfs.length);

          // Check for Excel files (for SMS link generation)
          const possibleExcelFiles = [
            path.join(folder, `${folder}_source.xlsx`),  // Folder-specific source file (PRIORITY)
            `${folder}_source.xlsx`,                     // Legacy location
            'Generic_Template_processed.xlsx',
            'Generic_Template.xlsx'
          ];
          
          // Add timestamped backup files
          const backupFiles = fs.readdirSync('.').filter(file => 
            file.startsWith('Generic_Template_backup_') && file.endsWith('.xlsx')
          );
          possibleExcelFiles.push(...backupFiles);

          let hasExcelFile = false;
          let excelFilePath = null;
          let hasFolderSpecificExcel = false;
          
          for (const excelFile of possibleExcelFiles) {
            if (fs.existsSync(excelFile)) {
              hasExcelFile = true;
              excelFilePath = excelFile;
              
              // Check if this is a folder-specific Excel file
              if (excelFile.includes(`${folder}_source.xlsx`)) {
                hasFolderSpecificExcel = true;
              }
              break;
            }
          }

          // Check if SMS links already generated and are up-to-date
          const smsLinksPath = path.join('letter_links', folder);
          let smsLinksGenerated = false;
          let smsLinksCount = 0;
          let smsFileExists = false;
          let smsLinksUpToDate = false;

          if (fs.existsSync(smsLinksPath)) {
            const smsFiles = fs.readdirSync(smsLinksPath);
            smsFileExists = smsFiles.includes('sms_batch.csv');
            smsLinksCount = smsFiles.filter(file => file.endsWith('.json') && file !== 'status.json').length;
            
            if (smsLinksCount > 0) {
              // Check if SMS links are up-to-date by comparing:
              // 1. SMS link count vs PDF count
              // 2. SMS generation time vs folder modification time
              
              const folderStats = fs.statSync(folder);
              let smsGenerationTime = null;
              
              // Try to get SMS generation time from status.json first (most accurate)
              const statusFilePath = path.join(smsLinksPath, 'status.json');
              if (fs.existsSync(statusFilePath)) {
                try {
                  const statusData = JSON.parse(fs.readFileSync(statusFilePath, 'utf8'));
                  smsGenerationTime = new Date(statusData.generatedAt);
                } catch (e) {
                  console.warn(`[WARN] Could not parse status.json for ${folder}:`, e.message);
                }
              }
              
              // Fallback to SMS folder modification time
              if (!smsGenerationTime) {
                const smsLinksStats = fs.statSync(smsLinksPath);
                smsGenerationTime = smsLinksStats.mtime;
              }
              
              // SMS links are considered up-to-date if:
              // - Count matches the PDF count
              // For regenerated SMS links, we don't need to check time since the user explicitly regenerated them
              const countMatches = smsLinksCount === totalPdfCount;
              
              // If counts match, SMS links are up-to-date
              // If counts don't match, SMS links are outdated regardless of time
              smsLinksUpToDate = countMatches;
              smsLinksGenerated = smsLinksUpToDate; // Only show as "generated" if up-to-date
              
              console.log(`[DEBUG] SMS status for ${folder}:`, {
                smsLinksCount,
                totalPdfCount,
                countMatches,
                smsTime: smsGenerationTime ? smsGenerationTime.toISOString() : 'unknown',
                folderTime: folderStats.mtime.toISOString(),
                smsLinksUpToDate
              });
            }
          }

          // Determine folder status
          let status = 'unknown';
          if (protectedCount > 0 && unprotectedCount > 0) {
            status = 'complete';
          } else if (protectedCount > 0 || unprotectedCount > 0) {
            status = 'partial';
          } else if (totalPdfCount > 0) {
            status = 'complete';
          }

          // Get folder timestamps
          const folderStats = fs.statSync(folder);

          return {
            name: folder,
            template: detectedTemplate.template,
            templateType: detectedTemplate.templateType,
            pdfCount: totalPdfCount,
            protectedCount: protectedCount,
            unprotectedCount: unprotectedCount,
            createdDate: folderStats.birthtime.toISOString(),
            lastModified: folderStats.mtime.toISOString(),
            status: status,
            hasExcelFile: hasExcelFile,
            hasFolderSpecificExcel: hasFolderSpecificExcel,
            excelFilePath: excelFilePath,
            smsLinksGenerated: smsLinksGenerated,
            smsLinksCount: smsLinksCount,
            smsFileExists: smsFileExists,
            smsLinksUpToDate: smsLinksUpToDate
          };

        } catch (error) {
          console.error(`[ERROR] Error analyzing folder ${folder}:`, error.message);
          return {
            name: folder,
            template: detectedTemplate.template,
            templateType: detectedTemplate.templateType,
            pdfCount: 0,
            protectedCount: 0,
            unprotectedCount: 0,
            createdDate: new Date().toISOString(),
            lastModified: new Date().toISOString(),
            status: 'error',
            hasExcelFile: false,
            hasFolderSpecificExcel: false,
            excelFilePath: null,
            smsLinksGenerated: false,
            smsLinksCount: 0,
            smsFileExists: false,
            smsLinksUpToDate: false
          };
        }
      })
      .filter(folder => folder.pdfCount > 0) // Only show folders with PDFs
      .sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified)); // Sort by newest first

    console.log(`[DEBUG] Enhanced folder scan complete: ${folders.length} folders found`);

    res.json({
      success: true,
      folders: folders,
      totalFolders: folders.length
    });

  } catch (error) {
    console.error('[ERROR] Enhanced folder scan failed:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to scan PDF folders',
      error: error.message
    });
  }
});

// API endpoint to send emails via Brevo
app.post('/api/send-emails-brevo', (req, res) => {
  // Set timeout for email sending (1 hour should be sufficient for large batches)
  req.setTimeout(3600000); // 1 hour in milliseconds
  res.setTimeout(3600000); // 1 hour in milliseconds

  const { emailData, folderName } = req.body;

  if (!emailData || !folderName) {
    return res.status(400).json({
      success: false,
      message: 'Email data and folder name are required'
    });
  }

  const folderPath = path.resolve('.', folderName);
  if (!fs.existsSync(folderPath)) {
    return res.status(404).json({
      success: false,
      message: 'PDF folder not found'
    });
  }

  try {
    // Create temporary JSON file with email data
    const emailDataFile = path.resolve('.', 'temp_email_data.json');
    fs.writeFileSync(emailDataFile, JSON.stringify(emailData, null, 2));

    console.log(`[DEBUG] Sending ${emailData.length} emails via Brevo`);
    console.log(`[DEBUG] PDF folder: ${folderPath}`);

    // Execute Brevo email service
    const python = spawn('python', [
      'brevo_email_service.py',
      '--data', emailDataFile,
      '--folder', folderPath,
      '--output', 'email_results.json'
    ], {
      encoding: 'utf8'
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log(`[BREVO] ${data.toString().trim()}`);
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`[BREVO ERROR] ${data.toString().trim()}`);
    });

    python.on('close', (code) => {
      console.log(`[DEBUG] Brevo service finished with code: ${code}`);

      // Clean up temp file
      try {
        if (fs.existsSync(emailDataFile)) {
          fs.unlinkSync(emailDataFile);
        }
      } catch (e) {
        console.warn('Could not clean up temp email data file');
      }

      if (code === 0) {
        // Try to read results
        let results = null;
        try {
          if (fs.existsSync('email_results.json')) {
            results = JSON.parse(fs.readFileSync('email_results.json', 'utf8'));
            fs.unlinkSync('email_results.json'); // Clean up
          }
        } catch (e) {
          console.warn('Could not read email results');
        }

        res.json({
          success: true,
          message: `Email sending completed`,
          results: results,
          stdout: stdout
        });
      } else {
        res.status(500).json({
          success: false,
          message: 'Failed to send emails via Brevo',
          error: stderr,
          stdout: stdout
        });
      }
    });

    python.on('error', (error) => {
      console.error('[ERROR] Failed to start Brevo email service:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to start email service',
        error: error.message
      });
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Failed to process email request',
      error: error.message
    });
  }
});

// API endpoint to combine PDFs
app.post('/api/combine-pdfs', (req, res) => {
  // Set timeout for PDF combining (30 minutes should be sufficient)
  req.setTimeout(1800000); // 30 minutes in milliseconds
  res.setTimeout(1800000); // 30 minutes in milliseconds

  const { folderName, outputName } = req.body;

  if (!folderName || !outputName) {
    return res.status(400).json({
      success: false,
      message: 'Folder name and output name are required'
    });
  }

  const folderPath = path.resolve('.', folderName);
  const outputFileName = `${outputName}.pdf`;

  if (!fs.existsSync(folderPath)) {
    return res.status(404).json({
      success: false,
      message: 'Folder not found'
    });
  }

  try {
    console.log(`[DEBUG] Starting combine PDFs process for folder: ${folderName}`);
    console.log(`[DEBUG] Folder path: ${folderPath}`);
    console.log(`[DEBUG] Output filename: ${outputFileName}`);

    // Use new folder-based approach with combined/ subfolder
    console.log(`[DEBUG] Using new folder-based PDF combining approach`);

    // Create combined folder if it doesn't exist
    const combinedPath = path.join(folderPath, 'combined');
    if (!fs.existsSync(combinedPath)) {
      fs.mkdirSync(combinedPath, { recursive: true });
      console.log(`[DEBUG] Created combined folder: ${combinedPath}`);
    }

    // Set output path in combined folder
    const outputPath = path.join(combinedPath, outputFileName);
    console.log(`[DEBUG] Output will be saved to: ${outputPath}`);

    // Check if unprotected folder exists
    const unprotectedPath = path.join(folderPath, 'unprotected');
    if (!fs.existsSync(unprotectedPath)) {
      return res.status(400).json({
        success: false,
        message: 'No unprotected folder found. Only unprotected PDFs can be combined (protected PDFs have individual passwords).'
      });
    }

    const unprotectedPdfs = fs.readdirSync(unprotectedPath)
      .filter(file => file.endsWith('.pdf'));

    if (unprotectedPdfs.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No PDF files found in unprotected folder'
      });
    }

    console.log(`[DEBUG] Found ${unprotectedPdfs.length} unprotected PDFs to combine`);
    console.log(`[DEBUG] Note: Protected PDFs excluded (each has unique password)`);

    // Use new folder-based Python script approach
    console.log(`[DEBUG] Combining ${unprotectedPdfs.length} PDFs from ${folderName}`);
    console.log(`[DEBUG] Output file: ${outputPath}`);

    const pythonArgs = [
      'combine_pdfs.py',
      '--folder', folderPath,
      '--name', outputName,
      '--output', outputPath
    ];

    console.log(`[DEBUG] Python command: python ${pythonArgs.join(' ')}`);
    console.log(`[DEBUG] Using folder-based approach (no temp JSON file needed)`);

    const python = spawn('python', pythonArgs, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      console.log(`[DEBUG] Python script finished with code: ${code}`);
      console.log(`[DEBUG] Python stdout: ${stdout}`);
      if (stderr) console.log(`[DEBUG] Python stderr: ${stderr}`);

      if (code === 0 && fs.existsSync(outputPath)) {
        res.json({
          success: true,
          message: `Combined ${unprotectedPdfs.length} unprotected PDFs successfully`,
          filename: outputFileName,
          folderPath: `${folderName}/combined`,
          fullPath: outputPath,
          pdfCount: unprotectedPdfs.length,
          note: 'Protected PDFs excluded (each has unique password)'
        });
      } else {
        res.status(500).json({
          success: false,
          message: 'Failed to combine PDFs',
          error: stderr || 'Unknown error occurred',
          stdout: stdout
        });
      }
    });

    python.on('error', (error) => {
      console.error('[ERROR] Failed to start Python process:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to start PDF combination process',
        error: error.message
      });
    });

  } catch (error) {
    console.error('[ERROR] Exception in combine PDFs endpoint:', error);
    console.error('[ERROR] Stack trace:', error.stack);
    res.status(500).json({
      success: false,
      message: 'Failed to combine PDFs',
      error: error.message,
      stack: error.stack
    });
  }
});

// Serve static files from dist directory (for production)
app.use(express.static(path.join(__dirname, 'dist')));

// Authentication endpoints removed temporarily to fix startup issues
// TODO: Re-enable authentication after PDF generation is working

// API endpoint to check server status
app.get('/api/status', (req, res) => {
  res.json({
    status: 'running',
    timestamp: new Date().toISOString(),
    outputDir: path.resolve(outputDir)
  });
});

// SMS Link Generation API endpoints
// API endpoint to generate SMS links
app.post('/api/generate-sms-links', (req, res) => {
  // Set timeout for SMS link generation (10 minutes should be sufficient)
  req.setTimeout(600000); // 10 minutes in milliseconds
  res.setTimeout(600000); // 10 minutes in milliseconds

  const { outputFolder, template } = req.body;

  if (!outputFolder || !template) {
    return res.status(400).json({
      success: false,
      message: 'Output folder and template are required'
    });
  }

  const folderPath = path.resolve('.', outputFolder);
  if (!fs.existsSync(folderPath)) {
    return res.status(404).json({
      success: false,
      message: 'Output folder not found. Please generate PDFs first.'
    });
  }

  try {
    console.log(`[DEBUG] Starting SMS link generation for folder: ${outputFolder}`);
    console.log(`[DEBUG] Template: ${template}`);

    // Execute SMS link generation script
    const pythonArgs = [
      'generate_sms_links.py',
      '--folder', outputFolder,
      '--template', template,
      '--base-url', `${req.protocol}://${req.get('host')}`
    ];

    console.log(`[DEBUG] Python command: python ${pythonArgs.join(' ')}`);

    const python = spawn('python', pythonArgs, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log(`[SMS] ${data.toString().trim()}`);
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`[SMS ERROR] ${data.toString().trim()}`);
    });

    python.on('close', (code) => {
      console.log(`[DEBUG] SMS link generation finished with code: ${code}`);

      if (code === 0) {
        // Check if SMS file was created
        const smsFilePath = path.join('letter_links', outputFolder, 'sms_batch.csv');
        const smsFileExists = fs.existsSync(smsFilePath);

        // Extract number of links generated from stdout
        const linksMatch = stdout.match(/Generated (\d+) SMS links/);
        const linksGenerated = linksMatch ? parseInt(linksMatch[1]) : 0;

        res.json({
          success: true,
          message: `Generated ${linksGenerated} SMS links successfully`,
          linksGenerated: linksGenerated,
          smsFileReady: smsFileExists,
          smsFilePath: smsFileExists ? smsFilePath : null,
          stdout: stdout
        });
      } else {
        res.status(500).json({
          success: false,
          message: 'Failed to generate SMS links',
          error: stderr || 'Unknown error occurred',
          stdout: stdout
        });
      }
    });

    python.on('error', (error) => {
      console.error('[ERROR] Failed to start SMS link generation:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to start SMS link generation process',
        error: error.message
      });
    });

  } catch (error) {
    console.error('[ERROR] Exception in SMS link generation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to generate SMS links',
      error: error.message
    });
  }
});

// NEW: Folder-based SMS link generation endpoint
app.post('/api/generate-sms-links-from-folder', (req, res) => {
  // Set timeout for SMS link generation (10 minutes should be sufficient)
  req.setTimeout(600000); // 10 minutes in milliseconds
  res.setTimeout(600000); // 10 minutes in milliseconds

  const { folderName, template, baseUrl } = req.body;

  if (!folderName) {
    return res.status(400).json({
      success: false,
      message: 'Folder name is required'
    });
  }

  const folderPath = path.resolve('.', folderName);
  if (!fs.existsSync(folderPath)) {
    return res.status(404).json({
      success: false,
      message: 'Selected folder not found. Please ensure the folder exists.'
    });
  }

  // Auto-detect template if not provided
  let detectedTemplate = template;
  if (!detectedTemplate) {
    const templateMapping = {
      'output_sph_': 'SPH_Fresh.py',
      'output_jph_': 'JPH_Fresh.py',
      'output_company_': 'Company_Fresh.py',
      'output_med_sph_': 'MED_SPH_Fresh_Signature.py',
      'output_med_jph_': 'MED_JPH_Fresh_Signature.py'
    };

    for (const [prefix, templateFile] of Object.entries(templateMapping)) {
      if (folderName.startsWith(prefix)) {
        detectedTemplate = templateFile;
        break;
      }
    }

    if (!detectedTemplate) {
      return res.status(400).json({
        success: false,
        message: 'Could not auto-detect template. Please specify template manually.'
      });
    }
  }

  try {
    console.log(`[DEBUG] Starting folder-based SMS link generation`);
    console.log(`[DEBUG] Folder: ${folderName}`);
    console.log(`[DEBUG] Template: ${detectedTemplate} (${template ? 'manual' : 'auto-detected'})`);

    const startTime = Date.now();

    // Execute SMS link generation script
    const pythonArgs = [
      'generate_sms_links.py',
      '--folder', folderName,
      '--template', detectedTemplate,
      '--base-url', baseUrl || `${req.protocol}://${req.get('host')}`
    ];

    console.log(`[DEBUG] Python command: python ${pythonArgs.join(' ')}`);

    const python = spawn('python', pythonArgs, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
      console.log(`[SMS-FOLDER] ${data.toString().trim()}`);
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
      console.error(`[SMS-FOLDER ERROR] ${data.toString().trim()}`);
    });

    python.on('close', (code) => {
      const endTime = Date.now();
      const processingTime = Math.round((endTime - startTime) / 1000);
      
      console.log(`[DEBUG] Folder-based SMS link generation finished with code: ${code}`);
      console.log(`[DEBUG] Processing time: ${processingTime} seconds`);

      if (code === 0) {
        // Check if SMS file was created
        const smsFilePath = path.join('letter_links', folderName, 'sms_batch.csv');
        const smsFileExists = fs.existsSync(smsFilePath);

        // Extract number of links generated from stdout
        const linksMatch = stdout.match(/Generated (\d+) SMS links/);
        const linksGenerated = linksMatch ? parseInt(linksMatch[1]) : 0;

        // Extract Excel file used from stdout
        const excelMatch = stdout.match(/Successfully loaded Excel file: ([^\s]+)/);
        const excelFileUsed = excelMatch ? excelMatch[1] : 'Unknown';

        // Create status file for tracking
        try {
          const statusData = {
            folderName: folderName,
            template: detectedTemplate,
            templateType: detectedTemplate.replace('_Fresh.py', '').replace('_Signature.py', ''),
            generatedAt: new Date().toISOString(),
            linksGenerated: linksGenerated,
            smsFileCreated: smsFileExists,
            smsFileName: 'sms_batch.csv',
            excelFileUsed: excelFileUsed,
            processingTimeSeconds: processingTime,
            linkExpiryDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
            baseUrl: baseUrl || `${req.protocol}://${req.get('host')}`,
            generatedBy: 'system' // TODO: Add user identification
          };

          const statusFilePath = path.join('letter_links', folderName, 'status.json');
          fs.writeFileSync(statusFilePath, JSON.stringify(statusData, null, 2));
          console.log(`[DEBUG] Status file created: ${statusFilePath}`);
        } catch (statusError) {
          console.warn(`[WARN] Could not create status file: ${statusError.message}`);
        }

        res.json({
          success: true,
          message: `Generated ${linksGenerated} SMS links successfully from folder ${folderName}`,
          folderName: folderName,
          template: detectedTemplate,
          linksGenerated: linksGenerated,
          smsFileReady: smsFileExists,
          smsFilePath: smsFileExists ? smsFilePath : null,
          processingTime: `${Math.floor(processingTime / 60)}m ${processingTime % 60}s`,
          excelFileUsed: excelFileUsed,
          stdout: stdout
        });
      } else {
        res.status(500).json({
          success: false,
          message: 'Failed to generate SMS links from folder',
          folderName: folderName,
          template: detectedTemplate,
          error: stderr || 'Unknown error occurred',
          stdout: stdout,
          processingTime: `${processingTime}s`
        });
      }
    });

    python.on('error', (error) => {
      console.error('[ERROR] Failed to start folder-based SMS link generation:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to start SMS link generation process',
        folderName: folderName,
        error: error.message
      });
    });

  } catch (error) {
    console.error('[ERROR] Exception in folder-based SMS link generation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to generate SMS links from folder',
      folderName: folderName,
      error: error.message
    });
  }
});

// API endpoint to download SMS bulk file
app.get('/api/download-sms-file/:outputFolder', (req, res) => {
  try {
    const { outputFolder } = req.params;
    const smsFilePath = path.join('letter_links', outputFolder, 'sms_batch.csv');

    if (!fs.existsSync(smsFilePath)) {
      return res.status(404).json({
        success: false,
        message: 'SMS file not found. Please generate SMS links first.'
      });
    }

    const stats = fs.statSync(smsFilePath);
    const filename = `SMS_Batch_${outputFolder}_${new Date().toISOString().split('T')[0]}.csv`;

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Length', stats.size);

    console.log(`[DEBUG] Downloading SMS file: ${smsFilePath} as ${filename}`);
    fs.createReadStream(smsFilePath).pipe(res);

  } catch (error) {
    console.error('[ERROR] Failed to download SMS file:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to download SMS file',
      error: error.message
    });
  }
});

// API endpoint to view individual letter (customer-facing)
app.get('/letter/:uniqueId', (req, res) => {
  try {
    const { uniqueId } = req.params;
    
    // Find the letter data file
    const letterLinksDir = 'letter_links';
    let letterData = null;
    let letterFile = null;

    // Search through all output folders for the letter
    if (fs.existsSync(letterLinksDir)) {
      const outputFolders = fs.readdirSync(letterLinksDir);
      
      for (const folder of outputFolders) {
        const folderPath = path.join(letterLinksDir, folder);
        if (fs.statSync(folderPath).isDirectory()) {
          const jsonFile = path.join(folderPath, `${uniqueId}.json`);
          if (fs.existsSync(jsonFile)) {
            letterFile = jsonFile;
            letterData = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
            break;
          }
        }
      }
    }

    if (!letterData) {
      return res.status(404).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Letter Not Found - NICL</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .error { color: #d32f2f; }
          </style>
        </head>
        <body>
          <h1 class="error">Letter Not Found</h1>
          <p>The requested letter could not be found or may have expired.</p>
          <p>Please contact NICL customer service for assistance.</p>
        </body>
        </html>
      `);
    }

    // Check if letter has expired
    const now = new Date();
    const expiresAt = new Date(letterData.expiresAt);
    
    if (now > expiresAt) {
      return res.status(410).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Letter Expired - NICL</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .error { color: #d32f2f; }
          </style>
        </head>
        <body>
          <h1 class="error">Letter Expired</h1>
          <p>This letter has expired and is no longer available.</p>
          <p>Please contact NICL customer service for assistance.</p>
        </body>
        </html>
      `);
    }

    // Check access limits
    if (letterData.accessCount >= letterData.maxAccess) {
      return res.status(410).send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Access Limit Exceeded - NICL</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .error { color: #d32f2f; }
          </style>
        </head>
        <body>
          <h1 class="error">Access Limit Exceeded</h1>
          <p>This letter has been accessed too many times and is no longer available.</p>
          <p>Please contact NICL customer service for assistance.</p>
        </body>
        </html>
      `);
    }

    // Increment access count
    letterData.accessCount = (letterData.accessCount || 0) + 1;
    fs.writeFileSync(letterFile, JSON.stringify(letterData, null, 2));

    // Serve the letter viewer HTML
    const letterHtml = generateLetterViewerHTML(letterData);
    res.send(letterHtml);

  } catch (error) {
    console.error('[ERROR] Failed to serve letter:', error);
    res.status(500).send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Error - NICL</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
          .error { color: #d32f2f; }
        </style>
      </head>
      <body>
        <h1 class="error">System Error</h1>
        <p>An error occurred while loading the letter.</p>
        <p>Please try again later or contact NICL customer service.</p>
      </body>
      </html>
    `);
  }
});

// Function to generate letter viewer HTML
function generateLetterViewerHTML(letterData) {
  const expiryDate = new Date(letterData.expiresAt).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  });

  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>NICL - ${letterData.letterType} Arrears Notice</title>
      <style>
        /* Base styles - Mobile First */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
          font-family: 'Cambria', 'Times New Roman', serif; 
          line-height: 1.4; 
          color: #000; 
          background-color: #f5f5f5;
          padding: 10px;
          padding-bottom: 120px; /* Space for fixed bottom buttons */
        }
        .container { 
          max-width: 100%; 
          margin: 0 auto; 
          background: white; 
          padding: 20px; 
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        /* Header with centered logo */
        .header { 
          text-align: center;
          margin-bottom: 30px;
          padding-bottom: 20px;
          border-bottom: 2px solid #0066cc;
        }
        .logo { 
          display: block;
          margin: 0 auto 15px auto;
          width: 120px;
          height: auto;
          max-width: 100%;
        }
        .company-name {
          font-size: 18pt;
          font-weight: bold;
          color: #0066cc;
          margin-top: 10px;
        }
        
        /* Date positioning */
        .date { 
          text-align: left; 
          margin-bottom: 20px; 
          font-weight: bold;
          font-size: 16pt;
          color: #333;
        }
        
        /* Address block */
        .address { 
          margin-bottom: 25px; 
          line-height: 1.3;
        }
        .address p { 
          margin-bottom: 5px; 
          font-weight: bold;
          font-size: 16pt;
          text-transform: uppercase;
        }
        
        /* Subject line */
        .subject { 
          font-weight: bold; 
          margin: 25px 0; 
          font-size: 18pt;
          text-decoration: underline;
          text-align: center;
          color: #333;
        }
        
        /* Salutation */
        .salutation { 
          margin-bottom: 20px; 
          font-size: 16pt;
          font-weight: bold;
        }
        
        /* Body content */
        .content { 
          margin-bottom: 20px; 
          text-align: justify;
          font-size: 15pt;
          line-height: 1.5;
        }
        
        /* Policy table */
        .policy-table { 
          width: 100%; 
          border-collapse: collapse; 
          margin: 25px 0; 
          font-size: 14pt;
          background: #f8f9fa;
        }
        .policy-table th, .policy-table td { 
          border: 2px solid #0066cc; 
          padding: 12px 8px; 
          text-align: center; 
          vertical-align: middle;
        }
        .policy-table th { 
          background-color: #0066cc; 
          color: white;
          font-weight: bold;
          font-size: 13pt;
        }
        .policy-table td {
          font-size: 14pt;
        }
        .policy-table td:last-child {
          font-weight: bold;
          color: #333;
          font-size: 16pt;
        }
        
        /* QR Code section */
        .qr-section { 
          text-align: center; 
          margin: 30px 0; 
          padding: 25px;
        }
        .qr-code { 
          width: 140px; 
          height: 140px; 
          margin: 15px auto;
          display: block;
        }
        .maucas-logo {
          width: 130px;
          height: auto;
          margin-bottom: 15px;
          display: block;
          margin-left: auto;
          margin-right: auto;
        }
        .zwenn-logo {
          width: 70px;
          height: auto;
          margin-top: 15px;
          display: block;
          margin-left: auto;
          margin-right: auto;
        }
        
        /* Action buttons - Fixed bottom bar */
        .actions { 
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(135deg, #0066cc, #004499);
          padding: 20px 15px;
          box-shadow: 0 -5px 20px rgba(0,0,0,0.3);
          z-index: 1000;
          text-align: center;
        }
        .btn { 
          display: block;
          width: 100%;
          max-width: 280px;
          margin: 8px auto;
          padding: 18px 20px;
          background-color: #ffffff; 
          color: #0066cc; 
          text-decoration: none; 
          border-radius: 25px; 
          font-size: 18pt;
          font-weight: bold;
          border: 3px solid #ffffff;
          box-shadow: 0 4px 15px rgba(0,0,0,0.2);
          transition: all 0.3s ease;
        }
        .btn:hover, .btn:active { 
          background-color: #f0f8ff;
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .btn.primary {
          background-color: #28a745;
          color: white;
          border-color: #28a745;
          font-size: 20pt;
          padding: 22px 25px;
          margin-bottom: 12px;
          animation: pulse 2s infinite;
        }
        .btn.primary:hover, .btn.primary:active {
          background-color: #218838;
          color: white;
        }
        
        /* Checkmark bullets for SPH/JPH */
        .checkmark-list {
          list-style: none;
          margin: 20px 0 20px 20px;
        }
        .checkmark-list li {
          position: relative;
          margin-bottom: 12px;
          padding-left: 25px;
          font-size: 15pt;
          line-height: 1.5;
        }
        .checkmark-list li:before {
          content: "✓";
          position: absolute;
          left: 0;
          color: #28a745;
          font-weight: bold;
          font-size: 16pt;
        }
        
        /* Footer */
        .footer { 
          text-align: center; 
          font-size: 13pt; 
          color: #666;
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid #ddd;
        }
        
        /* Pulse animation for primary button */
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7);
          }
          70% {
            box-shadow: 0 0 0 10px rgba(40, 167, 69, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(40, 167, 69, 0);
          }
        }
        
        /* Print styles */
        @media print {
          .actions { display: none; }
          body { padding-bottom: 0; background: white; }
          .container { box-shadow: none; }
        }
        
        /* Tablet styles */
        @media (min-width: 768px) {
          body {
            padding: 20px;
            padding-bottom: 120px;
          }
          .container {
            max-width: 700px;
            padding: 40px;
          }
          .logo {
            width: 150px;
          }
          .date {
            font-size: 18pt;
          }
          .subject {
            font-size: 20pt;
          }
          .content {
            font-size: 16pt;
          }
          .policy-table {
            font-size: 15pt;
          }
          .qr-code {
            width: 160px;
            height: 160px;
          }
        }
        
        /* Desktop styles */
        @media (min-width: 1024px) {
          body {
            padding-bottom: 0;
            background-color: #fff;
          }
          .container {
            max-width: 210mm;
            padding: 50px;
            margin: 20px auto;
          }
          .actions { 
            position: fixed;
            top: 20px;
            right: 20px;
            bottom: auto;
            left: auto;
            width: auto;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
          }
          .btn {
            display: inline-block;
            width: auto;
            margin: 0 5px 5px 0;
            padding: 12px 20px;
            font-size: 14pt;
          }
          .btn.primary {
            font-size: 16pt;
            padding: 15px 25px;
            margin-bottom: 5px;
            animation: none;
          }
          .logo {
            width: 120px;
          }
        }
      </style>
    </head>
    <body>
      <div class="actions">
        <a href="/api/download-pdf-unprotected/${letterData.id}" class="btn primary" target="_blank">
          📥 Download Letter
        </a>
        <a href="javascript:window.print()" class="btn">
          🖨️ Print
        </a>
      </div>

      <div class="container">
        <div class="header">
          <img src="/api/logo" alt="NICL Logo" class="logo" onerror="this.style.display='none'" />
          <div class="company-name">National Insurance Co. Ltd</div>
        </div>

        <div class="date">${letterData.date}</div>

        <div class="address">
          ${letterData.address.map(line => `<p>${line.toUpperCase()}</p>`).join('')}
        </div>

        <div class="subject">${letterData.subject}</div>

        <div class="salutation">${letterData.salutation}</div>

        <div class="content">
          <p>${letterData.bodyIntro}</p>
        </div>

        <table class="policy-table">
          <thead>
            <tr>
              <th>Policy No.</th>
              <th>Payment Frequency</th>
              <th>Premium Amount</th>
              <th>Total Premium in Arrears</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>${letterData.policyDetails.policyNo}</td>
              <td>${letterData.policyDetails.frequency}</td>
              <td>${letterData.policyDetails.premium}</td>
              <td><strong>${letterData.policyDetails.arrearsAmount}</strong></td>
            </tr>
          </tbody>
        </table>

        ${letterData.templateType === 'SPH' || letterData.templateType === 'JPH' ? `
          <div class="content">
            <p>Keeping your policy up to date is not only about making a payment. It ensures:</p>
            <ul class="checkmark-list">
              <li><strong>Continuity of Protection:</strong> You and your family remain covered against life's unexpected events. Even a short lapse could mean losing valuable protection just when it is most needed.</li>
              <li><strong>Growth of Your Savings:</strong> Every premium contributes to building long-term savings that support your financial goals, be it retirement, children's education, funding your dream project, or financial security.</li>
              <li><strong>Peace of Mind:</strong> By keeping your insurance policy lapse-free and premium up to date, you can live with confidence, knowing that your financial safety net is intact for you and your dear ones.</li>
            </ul>
            
            <p>Accordingly we encourage you to settle your outstanding premium at the earliest opportunity to ensure uninterrupted cover and continued growth of your savings and by acting now, you avoid the risk of:</p>
            <ul style="margin: 10px 0 10px 30px;">
              <li>Losing valuable accumulated benefits;</li>
              <li>Facing delays, reinstatement requirements, or medical reviews if the policy lapses; and</li>
              <li>Exposing your loved ones to uncertainty at a time when security matters most.</li>
            </ul>
            
            <p>Should you wish to avail of a facility to settle your arrears, kindly contact us on +230 602 3315 for assistance.</p>
          </div>
        ` : `
          <div class="content">
            <p>Maintaining timely payments ensures uninterrupted coverage and access to your benefits. Please arrange to settle the overdue amount to avoid any disruption to your Insurance Policy.</p>
          </div>
        `}

        ${letterData.qrCodeData ? `
          <div class="content">
            <p><strong>How to Settle Quickly and Easily?</strong></p>
            <p>Payment can be made through online, mobile app, branches or bank transfer. For your convenience, you may also settle payments instantly via the MauCAS QR Code (Scan to Pay) below using any mobile banking app such as Juice, MauBank WithMe, Blink, MyT Money, or other supported applications.</p>
          </div>
          
          <div class="qr-section">
            <img src="/api/maucas-logo" alt="MauCAS" class="maucas-logo" onerror="this.style.display='none'" />
            <div>
              <img id="qrcode" class="qr-code" src="/api/qr-code/${letterData.id}" alt="Payment QR Code" 
                   onload="console.log('QR code loaded successfully')" 
                   onerror="console.error('QR code failed to load'); this.style.display='none'; document.getElementById('qr-fallback').style.display='flex';" />
              <div id="qr-fallback" style="display: none; width: 100px; height: 100px; border: 2px dashed #ccc; margin: 10px auto; align-items: center; justify-content: center; font-size: 10pt; text-align: center; line-height: 1.2;">QR Code<br/>Available<br/>in PDF</div>
            </div>
            <img src="/api/zwenn-logo" alt="ZwennPay" class="zwenn-logo" onerror="this.style.display='none'" />
          </div>
        ` : `
          <div class="content">
            <p><strong>How to Settle Quickly and Easily?</strong></p>
            <p>Payment can be made through online, mobile app, branches or bank transfer. Please download the PDF version of this letter for the complete payment QR code.</p>
          </div>
          
          <div class="qr-section">
            <div style="width: 140px; height: 140px; border: 2px dashed #0066cc; margin: 15px auto; display: flex; align-items: center; justify-content: center; font-size: 12pt; text-align: center; line-height: 1.3; color: #0066cc; background-color: #f0f8ff;">
              <div>
                <strong>QR Code</strong><br/>
                Available in<br/>
                <strong>PDF Download</strong>
              </div>
            </div>
          </div>
        `}

        <div class="content">
          <p><em>If you have already settled this amount, please accept our thanks and disregard this reminder.</em></p>
          
          <p style="margin-top: 15px;">We appreciate your commitment for protection and financial wellbeing<br/><strong>NIC - Serving you, Serving the Nation</strong></p>
        </div>

        <div class="footer">
          <p><em>This is a computer generated statement and requires no signature</em></p>
        </div>
      </div>
    </body>
    </html>
  `;
}

// API endpoint to download PDF for letter viewer
app.get('/api/download-pdf/:uniqueId', (req, res) => {
  try {
    const { uniqueId } = req.params;
    
    // Find the letter data file to get PDF path
    const letterLinksDir = 'letter_links';
    let letterData = null;

    if (fs.existsSync(letterLinksDir)) {
      const outputFolders = fs.readdirSync(letterLinksDir);
      
      for (const folder of outputFolders) {
        const folderPath = path.join(letterLinksDir, folder);
        if (fs.statSync(folderPath).isDirectory()) {
          const jsonFile = path.join(folderPath, `${uniqueId}.json`);
          if (fs.existsSync(jsonFile)) {
            letterData = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
            break;
          }
        }
      }
    }

    if (!letterData || !letterData.pdfPath) {
      return res.status(404).json({
        success: false,
        message: 'PDF not found'
      });
    }

    // Convert relative path to absolute path
    const pdfPath = path.join('.', letterData.pdfPath.replace(/^\//, ''));
    
    if (!fs.existsSync(pdfPath)) {
      return res.status(404).json({
        success: false,
        message: 'PDF file not found on server'
      });
    }

    // Set headers for PDF download
    const filename = path.basename(pdfPath);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    console.log(`[DEBUG] Serving PDF: ${pdfPath} as ${filename}`);
    fs.createReadStream(pdfPath).pipe(res);

  } catch (error) {
    console.error('[ERROR] Failed to serve PDF:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to serve PDF',
      error: error.message
    });
  }
});

// Serve NICL logo
app.get('/api/logo', (req, res) => {
  const possibleLogos = ['NICLOGO2.jpg', 'NICLOGO.jpg', 'isphere_logo2.jpg', 'isphere_logo.jpg'];
  
  for (const logo of possibleLogos) {
    const logoPath = path.join(__dirname, logo);
    if (fs.existsSync(logoPath)) {
      res.sendFile(logoPath);
      return;
    }
  }
  
  res.status(404).send('Logo not found');
});

// Serve MauCAS logo
app.get('/api/maucas-logo', (req, res) => {
  const possibleLogos = ['maucas2.jpeg', 'maucas.jpeg'];
  
  for (const logo of possibleLogos) {
    const logoPath = path.join(__dirname, logo);
    if (fs.existsSync(logoPath)) {
      res.sendFile(logoPath);
      return;
    }
  }
  
  res.status(404).send('MauCAS logo not found');
});

// Serve ZwennPay logo
app.get('/api/zwenn-logo', (req, res) => {
  const logoPath = path.join(__dirname, 'zwennPay.jpg');
  if (fs.existsSync(logoPath)) {
    res.sendFile(logoPath);
  } else {
    res.status(404).send('ZwennPay logo not found');
  }
});

// Test QR code display (for debugging)
app.get('/test-qr', (req, res) => {
  const testHtmlPath = path.join(__dirname, 'test_qr_display.html');
  if (fs.existsSync(testHtmlPath)) {
    res.sendFile(testHtmlPath);
  } else {
    res.send('<h1>QR Test Page Not Found</h1><p>Please ensure test_qr_display.html exists in the project root.</p>');
  }
});

// Generate QR code image for letter viewer
app.get('/api/qr-code/:uniqueId', (req, res) => {
  try {
    const { uniqueId } = req.params;
    
    // Find the letter data file to get QR code data
    const letterLinksDir = 'letter_links';
    let letterData = null;

    if (fs.existsSync(letterLinksDir)) {
      const outputFolders = fs.readdirSync(letterLinksDir);
      
      for (const folder of outputFolders) {
        const folderPath = path.join(letterLinksDir, folder);
        if (fs.statSync(folderPath).isDirectory()) {
          const jsonFile = path.join(folderPath, `${uniqueId}.json`);
          if (fs.existsSync(jsonFile)) {
            letterData = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
            break;
          }
        }
      }
    }

    if (!letterData || !letterData.qrCodeData) {
      return res.status(404).send('QR code data not found');
    }

    console.log(`[DEBUG] Generating QR code for ${uniqueId}: ${letterData.qrCodeData.substring(0, 50)}...`);
    console.log(`[DEBUG] QR data length: ${letterData.qrCodeData.length} characters`);

    // Use Python to generate QR code image
    const pythonArgs = [
      '-c',
      `
import qrcode
import io
import sys
import base64

# QR data from command line
qr_data = """${letterData.qrCodeData.replace(/"/g, '\\"')}"""

# Generate QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=4,
    border=2,
)
qr.add_data(qr_data)
qr.make(fit=True)

# Create image
img = qr.make_image(fill_color="black", back_color="white")

# Save to bytes
img_buffer = io.BytesIO()
img.save(img_buffer, format='PNG')
img_buffer.seek(0)

# Output base64 encoded image
import base64
img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
print(img_base64)
      `
    ];

    const python = spawn('python', pythonArgs, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0 && stdout.trim()) {
        // Convert base64 to image and send
        const imageBuffer = Buffer.from(stdout.trim(), 'base64');
        res.setHeader('Content-Type', 'image/png');
        res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
        res.send(imageBuffer);
        console.log(`[DEBUG] QR code generated successfully for ${uniqueId}`);
      } else {
        console.error(`[ERROR] Python QR generation failed: ${stderr}`);
        // Fallback to a simple error image or redirect to Google Charts with truncated data
        const truncatedData = letterData.qrCodeData.substring(0, 1000); // Limit to 1000 chars
        const googleQRUrl = `https://chart.googleapis.com/chart?chs=100x100&cht=qr&chl=${encodeURIComponent(truncatedData)}`;
        res.redirect(googleQRUrl);
      }
    });

    python.on('error', (error) => {
      console.error('[ERROR] Failed to start Python QR generation:', error);
      // Fallback to Google Charts
      const truncatedData = letterData.qrCodeData.substring(0, 1000);
      const googleQRUrl = `https://chart.googleapis.com/chart?chs=100x100&cht=qr&chl=${encodeURIComponent(truncatedData)}`;
      res.redirect(googleQRUrl);
    });

  } catch (error) {
    console.error('[ERROR] Failed to generate QR code:', error);
    res.status(500).send('Failed to generate QR code');
  }
});

// Serve unprotected PDF (no password) for letter viewer
app.get('/api/download-pdf-unprotected/:uniqueId', (req, res) => {
  try {
    const { uniqueId } = req.params;
    
    // Find the letter data file to get PDF path
    const letterLinksDir = 'letter_links';
    let letterData = null;

    if (fs.existsSync(letterLinksDir)) {
      const outputFolders = fs.readdirSync(letterLinksDir);
      
      for (const folder of outputFolders) {
        const folderPath = path.join(letterLinksDir, folder);
        if (fs.statSync(folderPath).isDirectory()) {
          const jsonFile = path.join(folderPath, `${uniqueId}.json`);
          if (fs.existsSync(jsonFile)) {
            letterData = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
            break;
          }
        }
      }
    }

    if (!letterData || !letterData.pdfPath) {
      return res.status(404).json({
        success: false,
        message: 'PDF not found'
      });
    }

    // Convert to unprotected PDF path
    const unprotectedPdfPath = letterData.pdfPath.replace('/protected/', '/unprotected/');
    const pdfPath = path.join('.', unprotectedPdfPath.replace(/^\//, ''));
    
    if (!fs.existsSync(pdfPath)) {
      return res.status(404).json({
        success: false,
        message: 'Unprotected PDF file not found on server'
      });
    }

    // Set headers for PDF download
    const filename = path.basename(pdfPath);
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    console.log(`[DEBUG] Serving unprotected PDF: ${pdfPath} as ${filename}`);
    fs.createReadStream(pdfPath).pipe(res);

  } catch (error) {
    console.error('[ERROR] Failed to serve unprotected PDF:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to serve PDF',
      error: error.message
    });
  }
});

// Authentication API endpoints
app.post('/api/auth/send-otp', (req, res) => {
  try {
    const { email } = req.body;
    
    if (!email) {
      return res.status(400).json({
        success: false,
        message: 'Email is required'
      });
    }

    AuthService.sendOTP(email).then(result => {
      if (result.success) {
        res.json(result);
      } else {
        res.status(400).json(result);
      }
    }).catch(error => {
      console.error('[AUTH] Error sending OTP:', error);
      res.status(500).json({
        success: false,
        message: 'System error. Please try again later.'
      });
    });
  } catch (error) {
    console.error('[AUTH] Error in send-otp endpoint:', error);
    res.status(500).json({
      success: false,
      message: 'System error. Please try again later.'
    });
  }
});

app.post('/api/auth/verify-otp', (req, res) => {
  try {
    const { email, otp } = req.body;
    
    if (!email || !otp) {
      return res.status(400).json({
        success: false,
        message: 'Email and OTP are required'
      });
    }

    const result = AuthService.verifyOTP(email, otp);
    
    if (result.success) {
      res.json(result);
    } else {
      res.status(400).json(result);
    }
  } catch (error) {
    console.error('[AUTH] Error in verify-otp endpoint:', error);
    res.status(500).json({
      success: false,
      message: 'System error. Please try again later.'
    });
  }
});

app.post('/api/auth/password-login', (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password are required'
      });
    }

    const result = AuthService.passwordAuth(email, password);
    
    if (result.success) {
      res.json(result);
    } else {
      res.status(400).json(result);
    }
  } catch (error) {
    console.error('[AUTH] Error in password-login endpoint:', error);
    res.status(500).json({
      success: false,
      message: 'System error. Please try again later.'
    });
  }
});

// API endpoint to get folder contents (for file browser)
app.get('/api/folder-contents/:folder/:subfolder?', (req, res) => {
  try {
    const { folder, subfolder } = req.params;
    let targetPath;

    if (subfolder) {
      targetPath = path.join('.', folder, subfolder);
    } else {
      targetPath = path.join('.', folder);
    }

    if (!fs.existsSync(targetPath)) {
      return res.status(404).json({
        success: false,
        message: 'Folder not found'
      });
    }

    const files = fs.readdirSync(targetPath)
      .filter(file => file.endsWith('.pdf'))
      .map(file => {
        const filePath = path.join(targetPath, file);
        const stats = fs.statSync(filePath);
        return {
          filename: file,
          path: `${folder}${subfolder ? '/' + subfolder : ''}/${file}`,
          size: stats.size,
          lastModified: stats.mtime,
          location: subfolder || 'main'
        };
      });

    res.json({
      success: true,
      folder: folder,
      subfolder: subfolder || 'main',
      files: files,
      count: files.length
    });

  } catch (error) {
    console.error('Error reading folder contents:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to read folder contents',
      error: error.message
    });
  }
});

// API endpoint to get PDF file information (for download progress)
app.get('/api/pdf-info/:filename', (req, res) => {
  const filename = req.params.filename;

  // Search for the file in multiple possible locations
  const possiblePaths = [
    path.join(outputDir, filename),
    path.join('.', filename),
  ];

  // Add dynamic folder paths
  try {
    const currentDir = fs.readdirSync('.');
    const outputFolders = currentDir.filter(item => {
      return fs.statSync(item).isDirectory() &&
        (item.startsWith('output_') || item.startsWith('default_'));
    });

    outputFolders.forEach(folder => {
      // Check combined folder first (most likely location for downloads)
      possiblePaths.push(path.join('.', folder, 'combined', filename));
      possiblePaths.push(path.join('.', folder, filename));
      possiblePaths.push(path.join('.', folder, 'protected', filename));
      possiblePaths.push(path.join('.', folder, 'unprotected', filename));
    });
  } catch (error) {
    console.error('Error scanning for output folders:', error);
  }

  // Try each possible path
  let foundPath = null;
  for (const filePath of possiblePaths) {
    if (fs.existsSync(filePath)) {
      foundPath = filePath;
      break;
    }
  }

  if (foundPath) {
    const stats = fs.statSync(foundPath);
    const sizeInMB = (stats.size / (1024 * 1024)).toFixed(1);

    // Estimate download time based on file size (rough estimate)
    const estimatedSeconds = Math.ceil(stats.size / (1024 * 1024)); // 1MB per second estimate
    const estimatedTime = estimatedSeconds > 60
      ? `${Math.ceil(estimatedSeconds / 60)} minutes`
      : `${estimatedSeconds} seconds`;

    res.json({
      success: true,
      filename: filename,
      size: stats.size,
      sizeFormatted: `${sizeInMB} MB`,
      estimatedDownloadTime: estimatedTime,
      path: foundPath,
      lastModified: stats.mtime
    });
  } else {
    res.status(404).json({
      success: false,
      message: 'File not found',
      filename: filename
    });
  }
});

// API endpoint to check server status
app.get('/api/status', (req, res) => {
  res.json({
    status: 'running',
    timestamp: new Date().toISOString(),
    outputDir: path.resolve(outputDir)
  });
});

// Set user email for notifications
app.post('/api/set-user-email', (req, res) => {
  try {
    const { email, name } = req.body;
    
    if (!email || !email.includes('@')) {
      return res.status(400).json({
        success: false,
        message: 'Valid email address is required'
      });
    }
    
    // Set environment variables for the current session
    process.env.USER_EMAIL = email;
    process.env.USER_NAME = name || 'NICL User';
    
    console.log(`[EMAIL-CONFIG] User email set to: ${email}`);
    
    res.json({
      success: true,
      message: 'Email configuration saved successfully',
      email: email,
      name: name || 'NICL User'
    });
    
  } catch (error) {
    console.error('[ERROR] Failed to set user email:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to save email configuration',
      error: error.message
    });
  }
});

// Get current user email configuration
app.get('/api/get-user-email', (req, res) => {
  try {
    const userEmail = process.env.USER_EMAIL || '';
    const userName = process.env.USER_NAME || 'NICL User';
    
    res.json({
      success: true,
      email: userEmail,
      name: userName,
      configured: !!userEmail
    });
    
  } catch (error) {
    console.error('[ERROR] Failed to get user email:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get email configuration',
      error: error.message
    });
  }
});

// Serve React app for all non-API routes (except letter viewer)
app.get('*', (req, res) => {
  // Letter URLs should be handled by the letter route above - don't interfere
  if (req.path.startsWith('/letter/')) {
    // This should never be reached if the letter route is working
    console.error(`[ERROR] Letter URL reached catch-all route: ${req.path}`);
    return res.status(500).send('Letter route not working properly');
  }
  
  // API endpoints should return 404 if not found
  if (req.path.startsWith('/api/')) {
    return res.status(404).json({ error: 'API endpoint not found' });
  }
  
  // For all other routes (main app), redirect to Vite in development
  if (process.env.NODE_ENV === 'development') {
    res.redirect('http://localhost:5173');
  } else {
    // In production, serve the built React app
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  }
});

const server = app.listen(port, () => {
  console.log(`PDF Generation Server running at http://localhost:${port}`);
  console.log(`Output directory: ${path.resolve(outputDir)}`);

  if (isElectron) {
    console.log('Running in Electron environment');
  } else {
    console.log('Running in standard Node.js environment');
  }
});

// Set server timeout to 6 hours (21600000 ms) to handle large PDF generation jobs
server.timeout = 21600000; // 6 hours in milliseconds
server.keepAliveTimeout = 21600000; // 6 hours in milliseconds
server.headersTimeout = 21610000; // Slightly longer than keepAliveTimeout

console.log(`Server configured with 6-hour timeout for large PDF processing jobs`);