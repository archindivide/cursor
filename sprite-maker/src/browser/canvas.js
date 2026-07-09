import { getColor } from '../core/palette.js';

const MAX_DISPLAY = 512;

/**
 * @param {HTMLCanvasElement} canvas
 * @param {number} [maxDisplay]
 */
export function createCanvasRenderer(canvas, maxDisplay = MAX_DISPLAY) {
  const ctx = canvas.getContext('2d');
  if (!ctx) return { render: () => {}, pixelAt: () => null };

  let lastSize = 0;

  /**
   * @param {import('../core/sprite.js').Sprite} sprite
   */
  function render(sprite) {
    const size = sprite.getSize();
    if (size !== lastSize) {
      lastSize = size;
      const scale = Math.min(1, maxDisplay / size);
      const drawW = Math.floor(size * scale);
      const drawH = Math.floor(size * scale);
      canvas.width = drawW;
      canvas.height = drawH;
      canvas.style.width = drawW + 'px';
      canvas.style.height = drawH + 'px';
    }
    const w = canvas.width;
    const h = canvas.height;
    const scaleX = w / size;
    const scaleY = h / size;
    const imgData = ctx.createImageData(w, h);
    const data = imgData.data;
    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        const [r, g, b] = getColor(sprite.getPixel(px, py));
        const sx = Math.floor(px * scaleX);
        const sy = Math.floor(py * scaleY);
        const nx = Math.min(Math.floor((px + 1) * scaleX), w);
        const ny = Math.min(Math.floor((py + 1) * scaleY), h);
        for (let dy = sy; dy < ny; dy++) {
          for (let dx = sx; dx < nx; dx++) {
            const i = (dy * w + dx) * 4;
            data[i] = r;
            data[i + 1] = g;
            data[i + 2] = b;
            data[i + 3] = 255;
          }
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);
  }

  /**
   * @param {import('../core/sprite.js').Sprite} sprite
   * @param {number} clientX
   * @param {number} clientY
   * @returns {{ x: number, y: number } | null}
   */
  function pixelAt(sprite, clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const px = (clientX - rect.left) * (canvas.width / rect.width);
    const py = (clientY - rect.top) * (canvas.height / rect.height);
    const size = sprite.getSize();
    const scaleX = canvas.width / size;
    const scaleY = canvas.height / size;
    const x = Math.floor(px / scaleX);
    const y = Math.floor(py / scaleY);
    if (x >= 0 && x < size && y >= 0 && y < size) return { x, y };
    return null;
  }

  return { render, pixelAt };
}
