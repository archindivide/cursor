import { SIZES, PALETTE_SIZE, FORMAT_VERSION } from './constants.js';

const validSizes = new Set(SIZES);

/**
 * @param {number} size One of 32, 64, 128.
 * @returns {Sprite}
 */
export function createSprite(size) {
  return new Sprite(size);
}

/**
 * @typedef {Object} SpriteSaveData
 * @property {number} version
 * @property {32|64|128} size
 * @property {string} paletteRef
 * @property {number[][]} pixels
 */

export class Sprite {
  /**
   * @param {number} size One of 32, 64, 128.
   */
  constructor(size) {
    if (!validSizes.has(size)) {
      throw new Error(`Invalid size: ${size}. Use 32, 64, or 128.`);
    }
    this._size = size;
    this._pixels = Array.from({ length: size }, () =>
      Array.from({ length: size }, () => 0)
    );
  }

  /**
   * @returns {32|64|128}
   */
  getSize() {
    return this._size;
  }

  /**
   * @param {number} x
   * @param {number} y
   * @returns {number} Palette index 0–255.
   */
  getPixel(x, y) {
    if (!this._inBounds(x, y)) return 0;
    return this._pixels[y][x];
  }

  /**
   * @param {number} x
   * @param {number} y
   * @param {number} index Palette index 0–255.
   */
  setPixel(x, y, index) {
    if (!this._inBounds(x, y)) return;
    const idx = Math.floor(index);
    if (idx < 0 || idx >= PALETTE_SIZE) return;
    this._pixels[y][x] = idx;
  }

  _inBounds(x, y) {
    return (
      typeof x === 'number' &&
      typeof y === 'number' &&
      x >= 0 &&
      x < this._size &&
      y >= 0 &&
      y < this._size
    );
  }

  /**
   * @returns {number[][]} Raw 2D array of palette indices (row-major).
   */
  getData() {
    return this._pixels.map((row) => [...row]);
  }

  /**
   * @param {SpriteSaveData} data
   */
  load(data) {
    if (!data || typeof data !== 'object') return;
    const size = data.size;
    if (!validSizes.has(size)) return;
    const pixels = data.pixels;
    if (!Array.isArray(pixels) || pixels.length !== size) return;
    for (let i = 0; i < size; i++) {
      if (!Array.isArray(pixels[i]) || pixels[i].length !== size) return;
    }
    this._size = size;
    this._pixels = [];
    for (let y = 0; y < size; y++) {
      const row = [];
      for (let x = 0; x < size; x++) {
        let v = pixels[y][x];
        if (typeof v !== 'number' || v < 0 || v >= PALETTE_SIZE) v = 0;
        row.push(Math.floor(v));
      }
      this._pixels.push(row);
    }
  }

  /**
   * @returns {SpriteSaveData}
   */
  save() {
    return {
      version: FORMAT_VERSION,
      size: this._size,
      paletteRef: 'default',
      pixels: this.getData(),
    };
  }
}
