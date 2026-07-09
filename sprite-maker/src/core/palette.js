import { PALETTE_SIZE } from './constants.js';

/**
 * Default 256-color palette: 8×8×4 RGB reduced cube.
 * R,G: 8 levels (0,36,...,252); B: 4 levels (0,85,170,255).
 */
function buildDefaultPalette() {
  const palette = [];
  const rLevels = [0, 36, 72, 108, 144, 180, 216, 255];
  const gLevels = [0, 36, 72, 108, 144, 180, 216, 255];
  const bLevels = [0, 85, 170, 255];
  for (const b of bLevels) {
    for (const g of gLevels) {
      for (const r of rLevels) {
        palette.push([r, g, b]);
      }
    }
  }
  return palette;
}

let palette = buildDefaultPalette();

/**
 * @returns {number[][]} Copy of the full palette (array of [r,g,b]).
 */
export function getPalette() {
  return palette.map(([r, g, b]) => [r, g, b]);
}

/**
 * @param {number} index Palette index 0–255.
 * @returns {[number,number,number]} [r,g,b] or [0,0,0] if out of range.
 */
export function getColor(index) {
  if (typeof index !== 'number' || index < 0 || index >= PALETTE_SIZE) {
    return [0, 0, 0];
  }
  const [r, g, b] = palette[index];
  return [r, g, b];
}

/**
 * @param {number} index Palette index 0–255.
 * @param {number} r Red 0–255.
 * @param {number} g Green 0–255.
 * @param {number} b Blue 0–255.
 */
export function setColor(index, r, g, b) {
  if (typeof index !== 'number' || index < 0 || index >= PALETTE_SIZE) return;
  palette[index] = [
    Math.max(0, Math.min(255, Math.floor(r))),
    Math.max(0, Math.min(255, Math.floor(g))),
    Math.max(0, Math.min(255, Math.floor(b))),
  ];
}
