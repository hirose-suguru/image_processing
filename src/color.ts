import type { RgbColor } from './types';

export function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b]
    .map(x => x.toString(16).padStart(2, '0').toUpperCase())
    .join('');
}

export function hexToRgb(hex: string): RgbColor {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

export function isSimilarColor(
  r: number,
  g: number,
  b: number,
  targetColor: RgbColor,
  tolerance = 5,
): boolean {
  const dr = r - targetColor.r;
  const dg = g - targetColor.g;
  const db = b - targetColor.b;
  return Math.sqrt((dr * dr + dg * dg + db * db) / 3) <= tolerance;
}
