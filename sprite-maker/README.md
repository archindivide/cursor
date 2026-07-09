# Sprite Maker

JavaScript sprite creator with **32×32**, **64×64**, and **128×128** dimensions and a **256-color** indexed palette. Works in the browser (canvas UI) and in Node.js. Exposes a clear programmatic API for AI or scripts to create and manipulate sprites.

## Run the web app

```bash
npm start
```

Then open **http://localhost:3000/public/index.html** in your browser.

## Programmatic API (Node / AI)

Install or link the package, then:

```js
import { createSprite, getPalette } from 'sprite-maker';

const sprite = createSprite(32);
sprite.setPixel(0, 0, 42);
sprite.setPixel(1, 0, 42);
// ... AI or script generates indices ...

const data = sprite.save();
// persist or send to UI
```

### Core API

| Method | Description |
|--------|-------------|
| `createSprite(size)` | Create a new sprite. `size` must be `32`, `64`, or `128`. |
| `sprite.getSize()` | Returns `32`, `64`, or `128`. |
| `sprite.getPixel(x, y)` | Returns palette index (0–255) at `(x, y)`. |
| `sprite.setPixel(x, y, index)` | Set pixel at `(x, y)` to palette `index` (0–255). |
| `sprite.getData()` | Raw 2D array of palette indices (row-major). |
| `sprite.load(data)` | Load from structured JSON `data` (see schema below). |
| `sprite.save()` | Returns structured JSON object for export / AI. |

### Palette helpers

| Function | Description |
|----------|-------------|
| `getPalette()` | Returns full palette as `[r,g,b][]` (256 entries). |
| `getColor(index)` | Returns `[r, g, b]` for palette index `0–255`. |
| `setColor(index, r, g, b)` | Override a palette color (optional). |

### Constants

```js
import { SIZES, PALETTE_SIZE, FORMAT_VERSION } from 'sprite-maker';
// SIZES = [32, 64, 128]
// PALETTE_SIZE = 256
// FORMAT_VERSION = 1
```

## JSON schema (load / save)

Sprites are serialized as JSON. AI or other tools can generate or parse this format.

```json
{
  "version": 1,
  "size": 32,
  "paletteRef": "default",
  "pixels": [[0,1,2,...], ...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `version` | number | Format version (currently `1`). |
| `size` | number | Sprite width/height: `32`, `64`, or `128`. |
| `paletteRef` | string | Palette identifier (e.g. `"default"`). |
| `pixels` | `number[][]` | Row-major 2D array of palette indices (0–255). `pixels.length` and each `pixels[i].length` must equal `size`. |

- **Export**: Use **Export JSON** in the UI, or `sprite.save()` in code, then `JSON.stringify(data)`.
- **Import**: Use **Import JSON** (file or paste), or `sprite.load(JSON.parse(jsonText))` in code.

## Project layout

```
sprite-maker/
├── package.json
├── src/
│   ├── core/          # Environment-agnostic logic
│   │   ├── constants.js
│   │   ├── palette.js
│   │   └── sprite.js
│   ├── browser/       # Canvas UI
│   │   ├── app.js
│   │   ├── canvas.js
│   │   └── tools.js
│   └── index.js       # Re-exports for Node / AI
└── public/
    ├── index.html
    ├── main.js
    └── styles.css
```

## License

MIT
