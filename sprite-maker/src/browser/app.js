import { createSprite } from '../core/sprite.js';
import { getPalette, getColor } from '../core/palette.js';
import { SIZES } from '../core/constants.js';
import { createCanvasRenderer } from './canvas.js';
import { PENCIL, ERASER } from './tools.js';

/**
 * @param {Object} opts
 * @param {HTMLCanvasElement} opts.canvas
 * @param {HTMLElement} opts.sizeSelect
 * @param {HTMLElement} opts.paletteEl
 * @param {HTMLElement} opts.toolsEl
 * @param {HTMLButtonElement} opts.exportBtn
 * @param {HTMLInputElement} opts.importFile
 */
export function initApp(opts) {
  const {
    canvas,
    sizeSelect,
    paletteEl,
    toolsEl,
    exportBtn,
    importFile,
  } = opts;

  let sprite = createSprite(32);
  let selectedColorIndex = 0;
  let currentTool = PENCIL;
  let isDrawing = false;

  const { render, pixelAt } = createCanvasRenderer(canvas);

  function renderSprite() {
    render(sprite);
  }

  function buildSizeSelect() {
    sizeSelect.innerHTML = '';
    for (const size of SIZES) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = `${size}×${size}`;
      btn.dataset.size = String(size);
      if (size === sprite.getSize()) btn.classList.add('active');
      btn.addEventListener('click', () => {
        if (sprite.getSize() === size) return;
        if (!confirm('Create new sprite? Current work will be lost.')) {
          return;
        }
        sprite = createSprite(size);
        sizeSelect.querySelectorAll('[data-size]').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        renderSprite();
      });
      sizeSelect.appendChild(btn);
    }
  }

  function buildPalette() {
    paletteEl.innerHTML = '';
    const colors = getPalette();
    const size = Math.max(1, Math.floor(Math.sqrt(colors.length)));
    paletteEl.style.display = 'grid';
    paletteEl.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
    colors.forEach((_, i) => {
      const [r, g, b] = getColor(i);
      const swatch = document.createElement('button');
      swatch.type = 'button';
      swatch.className = 'palette-swatch';
      swatch.style.backgroundColor = `rgb(${r},${g},${b})`;
      swatch.title = `#${i}`;
      swatch.dataset.index = String(i);
      if (i === selectedColorIndex) swatch.classList.add('selected');
      swatch.addEventListener('click', () => {
        selectedColorIndex = i;
        paletteEl.querySelectorAll('.palette-swatch').forEach((s) => s.classList.remove('selected'));
        swatch.classList.add('selected');
      });
      paletteEl.appendChild(swatch);
    });
  }

  function buildTools() {
    toolsEl.innerHTML = '';
    const tools = [
      [PENCIL, 'Pencil'],
      [ERASER, 'Eraser'],
    ];
    for (const [id, label] of tools) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = label;
      btn.dataset.tool = id;
      if (id === currentTool) btn.classList.add('active');
      btn.addEventListener('click', () => {
        currentTool = id;
        toolsEl.querySelectorAll('[data-tool]').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
      });
      toolsEl.appendChild(btn);
    }
  }

  function applyTool(x, y) {
    const index = currentTool === ERASER ? 0 : selectedColorIndex;
    sprite.setPixel(x, y, index);
  }

  function handlePointer(clientX, clientY) {
    const pt = pixelAt(sprite, clientX, clientY);
    if (!pt) return;
    applyTool(pt.x, pt.y);
    renderSprite();
  }

  canvas.addEventListener('mousedown', (e) => {
    e.preventDefault();
    isDrawing = true;
    handlePointer(e.clientX, e.clientY);
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!isDrawing) return;
    handlePointer(e.clientX, e.clientY);
  });

  canvas.addEventListener('mouseup', () => {
    isDrawing = false;
  });
  canvas.addEventListener('mouseleave', () => {
    isDrawing = false;
  });

  exportBtn.addEventListener('click', () => {
    const data = sprite.save();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'sprite.json';
    a.click();
    URL.revokeObjectURL(a.href);
  });

  function doImport(jsonText) {
    try {
      const data = JSON.parse(jsonText);
      sprite.load(data);
      const size = sprite.getSize();
      sizeSelect.querySelectorAll('[data-size]').forEach((b) => {
        b.classList.toggle('active', Number(b.dataset.size) === size);
      });
      renderSprite();
    } catch (_) {
      alert('Invalid sprite JSON.');
    }
  }

  importFile.addEventListener('change', (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => doImport(String(r.result));
    r.readAsText(f);
    e.target.value = '';
  });

  buildSizeSelect();
  buildPalette();
  buildTools();
  renderSprite();
}
