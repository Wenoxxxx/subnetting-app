const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('subnetApi', {
  request: (payload) => ipcRenderer.invoke('subnet-request', payload),
});
