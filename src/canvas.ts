import type { RgbColor } from './types';

let canvasBackup: ImageData | null = null;

function getPinMarkerColor(pixelColor: RgbColor | null): string {
  if (!pixelColor) return 'red';
  const { r, g, b } = pixelColor;
  if (r > 150 && g < 100 && b < 100) return 'cyan';
  return 'red';
}

export function drawPinMarker(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  x: number,
  y: number,
  selectedColor: RgbColor | null,
): void {
  canvasBackup = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const markerColor = getPinMarkerColor(selectedColor);
  ctx.strokeStyle = markerColor;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(x, y, 8, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x - 12, y);
  ctx.lineTo(x + 12, y);
  ctx.moveTo(x, y - 12);
  ctx.lineTo(x, y + 12);
  ctx.stroke();
}

export function removePinMarker(ctx: CanvasRenderingContext2D): void {
  if (canvasBackup) {
    ctx.putImageData(canvasBackup, 0, 0);
    canvasBackup = null;
  }
}

export function loadImageToCanvas(
  file: File,
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  onLoad: (img: HTMLImageElement) => void,
): void {
  if (!file.type.match('image/(png|jpeg|jpg)')) {
    alert('PNG または JPEG/JPG 形式の画像を選択してください。');
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      onLoad(img);
    };
    img.onerror = () => alert('画像の読み込みに失敗しました。');
    img.src = e.target!.result as string;
  };
  reader.onerror = () => alert('ファイルの読み込みに失敗しました。');
  reader.readAsDataURL(file);
}
