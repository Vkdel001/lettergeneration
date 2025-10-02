import express from 'express';
import multer from 'multer';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import cors from 'cors';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 3001;

// Check if running in Electron
const isElectron = process.versions && process.versions.electron;

// Middleware
app.use(cors());
app.use(express.json());

// Configure multer for file uploads
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

const upload = multer({ storage });

// Ensure output directory exists
const outputDir = './generated_pdfs';
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// API endpoint to generate PDFs using Python
app.post('/api/generate-pdfs', upload.single('excelFile'), (req, res) => {
  const { template, outputFolder: customOutputFolder } = req.body;
  const inputFile = req.file.path;
  
  console.log(`[DEBUG] Received template: ${template}`);
  console.log(`[DEBUG] Received outputFolder: ${customOutputFolder}`);
  
  // Use custom output folder if provided, otherwise use default
  const outputFolder = customOutputFolder 
    ? path.resolve('.', customOutputFolder)
    : path.resolve(outputDir);
  
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

      res.json({
        success: true,
        message: `Generated ${pdfFiles.length} PDFs successfully`,
        files: pdfFiles,
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
    console.error(`[ERROR] Searched paths:`, possiblePaths);
    // Additional debug: check if the expected path exists
    const expectedPath = path.join('.', 'output_JPH_September2025', 'unprotected', filename);
    console.error(`[DEBUG] Expected path exists: ${fs.existsSync(expectedPath)} - ${expectedPath}`);
    res.status(404).json({ error: 'File not found' });
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
    // Only combine unprotected PDFs (since protected ones are identical but password-protected)
    let pdfFiles = [];
    let outputPath;
    
    // Check for unprotected subfolder first (new dual structure)
    const unprotectedPath = path.join(folderPath, 'unprotected');
    if (fs.existsSync(unprotectedPath) && fs.statSync(unprotectedPath).isDirectory()) {
      const unprotectedPdfs = fs.readdirSync(unprotectedPath)
        .filter(file => file.endsWith('.pdf'))
        .map(file => path.join(unprotectedPath, file));
      pdfFiles = unprotectedPdfs;
      outputPath = path.resolve(unprotectedPath, outputFileName);
      console.log(`[DEBUG] Found ${unprotectedPdfs.length} unprotected PDFs to combine`);
    } else {
      // Fallback to main folder (legacy structure)
      const directPdfs = fs.readdirSync(folderPath)
        .filter(file => file.endsWith('.pdf'))
        .map(file => path.join(folderPath, file));
      pdfFiles = directPdfs;
      outputPath = path.resolve(folderPath, outputFileName);
      console.log(`[DEBUG] Found ${directPdfs.length} PDFs in main folder (legacy structure)`);
    }
    
    if (pdfFiles.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'No PDF files found in the selected folder'
      });
    }
    
    console.log(`[DEBUG] Combining PDFs and saving to: ${outputPath}`);
    
    // Use dedicated Python script to combine PDFs
    console.log(`[DEBUG] Combining ${pdfFiles.length} PDFs from ${folderName}`);
    console.log(`[DEBUG] Output file: ${outputPath}`);
    
    const python = spawn('python', [
      'combine_pdfs.py',
      '--files', JSON.stringify(pdfFiles),
      '--output', outputPath
    ], {
      encoding: 'utf8'
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
          message: `Combined ${pdfFiles.length} PDFs successfully`,
          filename: outputFileName,
          folderPath: folderName,
          fullPath: outputPath,
          pdfCount: pdfFiles.length
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
    res.status(500).json({
      success: false,
      message: 'Failed to combine PDFs',
      error: error.message
    });
  }
});

// Serve static files from dist directory (for production)
app.use(express.static(path.join(__dirname, 'dist')));

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

app.listen(port, () => {
  console.log(`PDF Generation Server running at http://localhost:${port}`);
  console.log(`Output directory: ${path.resolve(outputDir)}`);
  
  if (isElectron) {
    console.log('Running in Electron environment');
  } else {
    console.log('Running in standard Node.js environment');
  }
});