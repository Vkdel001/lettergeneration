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

// Serve React app for all non-API routes
app.get('*', (req, res) => {
  // In development, redirect to Vite dev server
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