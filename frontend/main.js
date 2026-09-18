const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { PythonBridge } = require('./python-bridge');

let win = null;
let bridge = null;

function resolvePython() {
  // Packaged: pyinstaller binary next to resources.
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'subnet-cli', 'subnet-cli.exe');
  }
  // Dev: prefer backend/.venv python, fall back to system python on PATH.
  const venvPython = path.join(__dirname, '..', 'backend', '.venv', 'Scripts', 'python.exe');
  if (fs.existsSync(venvPython)) {
    return venvPython;
  }
  console.warn('[python] backend/.venv not found, falling back to system python. See README backend setup.');
  return 'python';
}

function createWindow() {
  win = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 1100,
    minHeight: 750,
    center: true,
    backgroundColor: '#1D2128',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
    },
  });
  win.loadFile(path.join(__dirname, 'src', 'index.html'));
}

app.whenReady().then(() => {
  const pythonCmd = resolvePython();
  const pythonArgs = app.isPackaged ? [] : ['-m', 'subnet_calc.cli'];
  const cwd = app.isPackaged
    ? undefined
    : path.join(__dirname, '..', 'backend', 'src');
  bridge = new PythonBridge(pythonCmd, pythonArgs, cwd);

  ipcMain.handle('subnet-request', (_event, request) => bridge.send(request));

  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (bridge) bridge.dispose();
  if (process.platform !== 'darwin') app.quit();
});
