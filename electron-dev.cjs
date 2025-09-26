#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

console.log('🚀 Starting NIC PDF Generator in Electron Development Mode...\n');

// Set environment variable for development
process.env.ELECTRON_IS_DEV = 'true';
process.env.NODE_ENV = 'development';

let server;
let electron;

// Function to check if server is running
function checkServer(callback) {
  const req = http.get('http://localhost:3001/api/status', (res) => {
    callback(true);
  });
  
  req.on('error', () => {
    callback(false);
  });
  
  req.setTimeout(1000, () => {
    req.destroy();
    callback(false);
  });
}

// Function to wait for server
function waitForServer(callback, attempts = 0) {
  if (attempts > 30) {
    console.log('❌ Server failed to start after 30 seconds');
    process.exit(1);
    return;
  }
  
  checkServer((isRunning) => {
    if (isRunning) {
      console.log('✅ Server is ready!');
      callback();
    } else {
      console.log(`⏳ Waiting for server... (${attempts + 1}/30)`);
      setTimeout(() => waitForServer(callback, attempts + 1), 1000);
    }
  });
}

// Start the server first
console.log('📡 Starting Node.js server...');
server = spawn('node', ['server.js'], {
  stdio: ['inherit', 'inherit', 'inherit'],
  env: { ...process.env },
  shell: true
});

server.on('error', (error) => {
  console.error('❌ Failed to start server:', error);
  process.exit(1);
});

// Wait for server to be ready, then start Electron
waitForServer(() => {
  console.log('🖥️  Starting Electron app...');
  
  // Use npx to run electron - handles paths with spaces better
  electron = spawn('npx', ['electron', '.'], {
    stdio: 'inherit',
    env: { ...process.env },
    shell: true
  });

  electron.on('close', (code) => {
    console.log('🔴 Electron closed, shutting down server...');
    if (server) {
      server.kill();
    }
    process.exit(0);
  });

  electron.on('error', (error) => {
    console.error('❌ Failed to start Electron:', error);
    if (server) {
      server.kill();
    }
    process.exit(1);
  });
});

// Handle process termination
function cleanup() {
  console.log('\n🔴 Shutting down...');
  if (electron) {
    electron.kill();
  }
  if (server) {
    server.kill();
  }
  process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);