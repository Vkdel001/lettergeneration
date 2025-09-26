const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 Starting NIC PDF Generator...\n');

// Kill any existing processes
function killExistingProcesses() {
    try {
        spawn('taskkill', ['/f', '/im', 'NIC PDF Generator.exe'], { stdio: 'ignore' });
        spawn('taskkill', ['/f', '/im', 'node.exe'], { stdio: 'ignore' });
    } catch (e) {
        // Ignore errors
    }
}

// Start server
function startServer() {
    console.log('📡 Starting server...');
    const server = spawn('node', ['server.js'], {
        stdio: 'inherit'
    });
    
    server.on('error', (error) => {
        console.error('❌ Failed to start server:', error);
    });
    
    return server;
}

// Start Electron app
function startElectronApp() {
    const appPath = path.join(__dirname, 'dist-electron', 'win-unpacked', 'NIC PDF Generator.exe');
    
    if (!fs.existsSync(appPath)) {
        console.error('❌ NIC PDF Generator.exe not found!');
        console.log('Please run: npm run dist');
        process.exit(1);
    }
    
    console.log('🖥️  Starting desktop app...');
    const app = spawn(appPath, [], {
        stdio: 'ignore',
        detached: true
    });
    
    app.on('error', (error) => {
        console.error('❌ Failed to start app:', error);
    });
    
    return app;
}

// Main execution
async function main() {
    killExistingProcesses();
    
    // Wait a moment
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Start server
    const server = startServer();
    
    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Start app
    const app = startElectronApp();
    
    console.log('✅ App launched successfully!');
    console.log('You can close this terminal window.');
    
    // Handle cleanup
    process.on('SIGINT', () => {
        console.log('\n🔴 Shutting down...');
        if (server) server.kill();
        if (app) app.kill();
        process.exit(0);
    });
}

main().catch(console.error);