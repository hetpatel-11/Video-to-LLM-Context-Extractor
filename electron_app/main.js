const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

function createWindow () {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      enableRemoteModule: false,
      nodeIntegration: false, // Ensure Node.js integration is off in renderer for security
    }
  });

  mainWindow.loadFile('index.html');

  // Open DevTools - remove for production
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('run-conversion', async (event, { videoPath, outputBasename, frameInterval, maxPages, maxFilesizeMb }) => {
  return new Promise((resolve, reject) => {
    // Adjust the path to your Python executable and script as necessary
    // If Python is in PATH, 'python' or 'python3' might be enough.
    // If using a venv, you'd point to venv/bin/python
    const venvPythonDir = path.join(__dirname, '..', 'venv', process.platform === 'win32' ? 'Scripts' : 'bin');
    const pythonExecutable = path.join(venvPythonDir, process.platform === 'win32' ? 'python.exe' : 'python');
    const scriptPath = path.join(__dirname, '..', 'src', 'video_to_pdf.py'); // Path to the python script

    console.log(`Running Python script: ${pythonExecutable} ${scriptPath}`);
    console.log(`Arguments: --video "${videoPath}" --output "${outputBasename}" --frame-interval ${frameInterval} --max-pages ${maxPages} --max-filesize ${maxFilesizeMb}`);

    const pythonProcess = spawn(pythonExecutable, [
      scriptPath,
      '--video', videoPath,
      '--output', outputBasename,
      '--frame-interval', frameInterval.toString(),
      '--max-pages', maxPages.toString(),
      '--max-filesize', maxFilesizeMb.toString()
    ]);

    let stdoutData = '';
    let stderrData = '';

    pythonProcess.stdout.on('data', (data) => {
      stdoutData += data.toString();
      console.log(`Python stdout: ${data}`);
      event.sender.send('conversion-progress', data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
      stderrData += data.toString();
      console.error(`Python stderr: ${data}`);
      event.sender.send('conversion-error', data.toString());
    });

    pythonProcess.on('close', (code) => {
      console.log(`Python script exited with code ${code}`);
      if (code === 0) {
        resolve({ success: true, message: stdoutData, outputDir: path.dirname(outputBasename) });
      } else {
        reject(new Error(`Python script failed with code ${code}. Error: ${stderrData || stdoutData}`));
      }
    });

    pythonProcess.on('error', (err) => {
      console.error('Failed to start Python process.', err);
      reject(new Error(`Failed to start Python process: ${err.message}`));
    });
  });
});

ipcMain.handle('select-video-file', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Videos', extensions: ['mp4', 'avi', 'mov', 'mkv', 'webm'] }
    ]
  });
  if (canceled || filePaths.length === 0) {
    return null;
  }
  return filePaths[0];
});

ipcMain.handle('select-output-directory', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog({
        properties: ['openDirectory', 'createDirectory']
    });
    if (canceled || filePaths.length === 0) {
        return null;
    }
    return filePaths[0];
}); 