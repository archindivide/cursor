import { initApp } from '../src/browser/app.js';

initApp({
  canvas: document.getElementById('canvas'),
  sizeSelect: document.getElementById('sizeSelect'),
  paletteEl: document.getElementById('paletteEl'),
  toolsEl: document.getElementById('toolsEl'),
  exportBtn: document.getElementById('exportBtn'),
  importFile: document.getElementById('importFile'),
});
