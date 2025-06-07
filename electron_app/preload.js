const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  runConversion: (args) => ipcRenderer.invoke('run-conversion', args),
  selectVideoFile: () => ipcRenderer.invoke('select-video-file'),
  selectOutputDirectory: () => ipcRenderer.invoke('select-output-directory'),
  onConversionProgress: (callback) => ipcRenderer.on('conversion-progress', (_event, value) => callback(value)),
  onConversionError: (callback) => ipcRenderer.on('conversion-error', (_event, value) => callback(value)),
  removeConversionProgressListener: () => ipcRenderer.removeAllListeners('conversion-progress'),
  removeConversionErrorListener: () => ipcRenderer.removeAllListeners('conversion-error')
}); 