const { app, BrowserWindow } = require('electron');
const path = require('node:path');

function createWindow () {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // In production, we load the built React files. In development we load localhost.
  const isDev = process.env.NODE_ENV !== 'production';
  
  if (isDev) {
    win.loadURL('http://localhost:3000');
  } else {
    // Note: Assuming frontend build output goes to frontend/dist 
    // Need to adjust path depending on monorepo build setup
    win.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
