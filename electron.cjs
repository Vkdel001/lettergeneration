const { app, BrowserWindow, Menu } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Check if running in development or production
const isDev = process.env.NODE_ENV === 'development' || process.env.ELECTRON_IS_DEV;
const isPackaged = app.isPackaged;

console.log('Environment check:');
console.log('- isDev:', isDev);
console.log('- isPackaged:', isPackaged);
console.log('- __dirname:', __dirname);
console.log('- process.resourcesPath:', process.resourcesPath);

let mainWindow;
let serverProcess;

let windowCreated = false;
let serverCheckInProgress = false;

function createWindow() {
  // Prevent multiple windows from being created
  if (windowCreated || mainWindow) {
    console.log('Window already exists, skipping creation');
    return;
  }
  
  windowCreated = true;
  console.log('Creating new Electron window...');
  
  // Determine icon path based on environment
  let iconPath;
  if (isPackaged) {
    iconPath = path.join(process.resourcesPath, 'app', 'src', 'nic2.jpeg');
  } else {
    iconPath = path.join(__dirname, 'src', 'nic2.jpeg');
  }
  
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true
    },
    icon: iconPath,
    show: false, // Don't show until ready
    titleBarStyle: 'default'
  });

  // Load the app - always use the Node.js server
  const startUrl = 'http://localhost:3001';

  console.log('Loading URL:', startUrl);
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus on window
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    windowCreated = false;
  });

  // Create application menu
  createMenu();
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Excel File',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            // Send message to renderer to trigger file dialog
            if (mainWindow) {
              mainWindow.webContents.send('trigger-file-dialog');
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About NIC PDF Generator',
          click: () => {
            // Show about dialog
            const { dialog } = require('electron');
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About NIC PDF Generator',
              message: 'NIC PDF Generator',
              detail: 'Version 1.0.0\nNational Insurance Company\nPDF Generation System'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function checkServerRunning(callback) {
  const http = require('http');
  const req = http.get('http://localhost:3001/api/status', (res) => {
    console.log('✅ Server is already running');
    callback(true);
  });
  
  req.on('error', () => {
    console.log('❌ Server is not running, will start it');
    callback(false);
  });
  
  req.setTimeout(2000, () => {
    req.destroy();
    callback(false);
  });
}

function startServer() {
  console.log('Checking if server is running...');
  
  checkServerRunning((isRunning) => {
    if (isRunning) {
      console.log('Server already running, proceeding to create window');
      return;
    }
    
    console.log('Starting Node.js server...');
    
    // Determine server path based on environment
    let serverPath;
    if (isPackaged) {
      // When packaged, server.js is in the distribution root (parent of app folder)
      serverPath = path.join(process.resourcesPath, '..', '..', 'server.js');
    } else {
      serverPath = path.join(__dirname, 'server.js');
    }
    
    if (!fs.existsSync(serverPath)) {
      console.error('Server file not found:', serverPath);
      return;
    }

    const workingDir = isPackaged 
      ? path.join(process.resourcesPath, '..', '..')
      : __dirname;

    serverProcess = spawn('node', [serverPath], {
      cwd: workingDir,
      stdio: 'inherit'
    });

    serverProcess.on('error', (error) => {
      console.error('Failed to start server:', error);
    });

    serverProcess.on('close', (code) => {
      console.log(`Server process exited with code ${code}`);
    });
  });
}

function waitForServerAndCreateWindow() {
  // Prevent multiple simultaneous checks
  if (serverCheckInProgress || windowCreated) {
    return;
  }
  
  serverCheckInProgress = true;
  
  checkServerRunning((isRunning) => {
    serverCheckInProgress = false;
    
    if (isRunning && !windowCreated) {
      console.log('✅ Server ready, creating window...');
      createWindow();
    } else if (!isRunning && !windowCreated) {
      console.log('⏳ Waiting for server...');
      setTimeout(() => waitForServerAndCreateWindow(), 2000);
    }
  });
}

// App event handlers
app.whenReady().then(() => {
  console.log('🚀 Electron ready, checking for server...');
  console.log('Is packaged:', isPackaged);
  console.log('Resources path:', process.resourcesPath);
  
  // Start server and wait for it to be ready
  startServer();
  setTimeout(() => waitForServerAndCreateWindow(), 3000);
});

app.on('window-all-closed', () => {
  // Kill server process if it exists
  if (serverProcess) {
    console.log('Terminating server process...');
    serverProcess.kill();
  }
  
  // On macOS, keep app running even when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS, re-create window when dock icon is clicked
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    console.log('Blocked new window creation to:', navigationUrl);
  });
});

// Handle app certificate errors
app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
  if (url.startsWith('http://localhost')) {
    // Allow localhost certificates
    event.preventDefault();
    callback(true);
  } else {
    callback(false);
  }
});