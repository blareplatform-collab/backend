const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Add any secure IPC commands here
    // e.g., getSecureStorage: (key) => ipcRenderer.invoke('get-secure', key)
});
