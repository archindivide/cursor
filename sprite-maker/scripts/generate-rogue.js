/**
 * Generate a 32×32 rogue sprite using the sprite-maker API.
 * Run: node scripts/generate-rogue.js
 * Then import public/rogue.json in the web app.
 */
import { createSprite } from '../src/index.js';
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { join, dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, '..', 'public', 'rogue.json');

// Palette indices (8×8×4 default): 0=black, 3=dark red, 10=dark brown, 20=mid brown,
// 73=dark gray, 83=skin, 101=light skin, 173=silver, 255=white
const C = {
  black: 0,
  outline: 0,
  cloakDark: 3,
  cloakMid: 10,
  cloakLight: 20,
  hoodShadow: 73,
  skin: 83,
  skinLight: 101,
  dagger: 173,
  white: 255,
};

const sprite = createSprite(32);

// 32×32 rogue: front-facing, hooded, clasped cloak, dagger. . = skip, o = outline,
// O = cloak dark, m = cloak mid, w = eyes, s = skin, d = dagger
const art = [
  '................................',
  '................................',
  '................oooo..............',
  '..............oooooOOO.............',
  '............oooOOOOOOOoo...........',
  '..........oooOOO.....OOOoo.........',
  '........oooOOO.......OOOooo........',
  '........oooOOO..ww..OOOooo.........', // eyes
  '........oooOOO..ww..OOOooo.........',
  '........oooOOOwwwwwwOOOooo.........',
  '..........oooOOOOOOOOoo...........',
  '............ooOOOOOOoo............',
  '............ooOssOOssoo............', // face
  '............ooOssOOssoo............',
  '..........oooOOssOOssooo..........',
  '..........oooOOssOOssooo..........',
  '............ooOOOOOOoo............',
  '..............ooOOoo..............',
  '............ooommmooommmoo........', // cloak
  '..........ooommmmmmmmmmooo........',
  '..........ooommmmmmmmmmooo........',
  '............ooommmmmmooo..........',
  '..............ooommmoo............',
  '................oomm..............',
  '..............ooommmoo............',
  '............ooommmmmmoo...........',
  '............ooommmmmmoo...........',
  '..............ooommmoo............',
  '............oo..dd..oo............', // dagger
  '............oo..dd..oo............',
  '..............oo....oo............',
  '................................',
  '................................',
];

const key = { o: C.outline, O: C.cloakDark, m: C.cloakMid, w: C.white, s: C.skin, d: C.dagger, '.': -1 };

for (let y = 0; y < 32; y++) {
  const row = art[y] || '';
  for (let x = 0; x < 32; x++) {
    const k = row[x];
    const idx = key[k] ?? -1;
    if (idx >= 0) sprite.setPixel(x, y, idx);
  }
}

// Hood interior (dark)
for (let y = 6; y <= 11; y++) {
  for (let x = 13; x <= 18; x++) {
    if (sprite.getPixel(x, y) === C.black) sprite.setPixel(x, y, C.hoodShadow);
  }
}

// Blade
sprite.setPixel(16, 28, C.dagger);
sprite.setPixel(17, 28, C.dagger);
sprite.setPixel(16, 29, C.dagger);
sprite.setPixel(17, 29, C.dagger);

const data = sprite.save();
writeFileSync(OUT, JSON.stringify(data, null, 2), 'utf8');
console.log('Wrote', OUT);

// ASCII preview (palette index → char)
const preview = { 0: '.', 3: '#', 10: '%', 20: '+', 73: ':', 83: '=', 101: '-', 173: '*', 255: '@' };
console.log('\nRogue sprite preview (32×32):\n');
for (let y = 0; y < 32; y++) {
  let line = '';
  for (let x = 0; x < 32; x++) {
    const i = sprite.getPixel(x, y);
    line += preview[i] ?? '?';
  }
  console.log(line);
}
console.log('\nRun "npm start", open http://localhost:3000/public/index.html, then Import JSON → rogue.json');
