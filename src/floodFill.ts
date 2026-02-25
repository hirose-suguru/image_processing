import type { RgbColor } from './types';
import { isSimilarColor } from './color';

export function floodFillReplace(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  startX: number,
  startY: number,
  targetColor: RgbColor,
  newColor: RgbColor,
  newAlpha: number,
  boundaryThreshold: number,
  colorTolerance: number,
): number {
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  const width = canvas.width;
  const height = canvas.height;
  const visited = new Uint8Array(width * height);
  const queue: number[] = [];
  let qHead = 0;
  let replacedCount = 0;

  const startIdx = startY * width + startX;
  queue.push(startIdx);
  visited[startIdx] = 1;

  while (qHead < queue.length) {
    const pos = queue[qHead++];
    const cx = pos % width;
    const cy = (pos / width) | 0;
    const idx = pos * 4;

    const pr = data[idx];
    const pg = data[idx + 1];
    const pb = data[idx + 2];

    if (isSimilarColor(pr, pg, pb, targetColor, colorTolerance)) {
      data[idx] = newColor.r;
      data[idx + 1] = newColor.g;
      data[idx + 2] = newColor.b;
      data[idx + 3] = newAlpha;
      replacedCount++;
    }

    const neighbors = [cx - 1, cy, cx + 1, cy, cx, cy - 1, cx, cy + 1];
    for (let n = 0; n < 8; n += 2) {
      const nx = neighbors[n];
      const ny = neighbors[n + 1];
      if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
      const nIdx = ny * width + nx;
      if (visited[nIdx]) continue;
      visited[nIdx] = 1;

      const ni = nIdx * 4;
      const dr = data[ni] - targetColor.r;
      const dg = data[ni + 1] - targetColor.g;
      const db = data[ni + 2] - targetColor.b;
      const distance = Math.sqrt((dr * dr + dg * dg + db * db) / 3);

      if (distance > boundaryThreshold) continue;
      queue.push(nIdx);
    }
  }

  ctx.putImageData(imageData, 0, 0);
  return replacedCount;
}

export function floodFillTransparent(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  startX: number,
  startY: number,
  targetColor: RgbColor,
  boundaryThreshold: number,
  colorTolerance: number,
): number {
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imageData.data;
  const width = canvas.width;
  const height = canvas.height;
  const visited = new Uint8Array(width * height);
  const queue: number[] = [];
  let qHead = 0;
  let replacedCount = 0;

  const startIdx = startY * width + startX;
  queue.push(startIdx);
  visited[startIdx] = 1;

  while (qHead < queue.length) {
    const pos = queue[qHead++];
    const cx = pos % width;
    const cy = (pos / width) | 0;
    const idx = pos * 4;

    if (isSimilarColor(data[idx], data[idx + 1], data[idx + 2], targetColor, colorTolerance)) {
      data[idx + 3] = 0;
      replacedCount++;
    }

    const neighbors = [cx - 1, cy, cx + 1, cy, cx, cy - 1, cx, cy + 1];
    for (let n = 0; n < 8; n += 2) {
      const nx = neighbors[n];
      const ny = neighbors[n + 1];
      if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
      const nIdx = ny * width + nx;
      if (visited[nIdx]) continue;
      visited[nIdx] = 1;

      const ni = nIdx * 4;
      const dr = data[ni] - targetColor.r;
      const dg = data[ni + 1] - targetColor.g;
      const db = data[ni + 2] - targetColor.b;
      const distance = Math.sqrt((dr * dr + dg * dg + db * db) / 3);

      if (distance > boundaryThreshold) continue;
      queue.push(nIdx);
    }
  }

  ctx.putImageData(imageData, 0, 0);
  return replacedCount;
}
