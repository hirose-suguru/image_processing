import type { RgbaColor, PinPosition, ReplaceMode } from './types';
import { isSimilarColor, hexToRgb, rgbToHex } from './color';
import { floodFillReplace, floodFillTransparent } from './floodFill';
import { drawPinMarker, removePinMarker } from './canvas';
import { updateMessage } from './ui';

type ReplaceContext = {
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  selectedColor: RgbaColor | null;
  pinPosition: PinPosition | null;
  currentReplaceMode: ReplaceMode;
  chainModeChecked: boolean;
  newColorInputValue: string;
  alphaSliderValue: string;
  boundaryThresholdValue: string;
  replaceBtn: HTMLButtonElement;
  transparentBtn: HTMLButtonElement;
  onChainUpdate: (newColor: RgbaColor) => void;
};

export function replaceColor(ctx_: ReplaceContext): void {
  const {
    canvas, ctx, selectedColor, pinPosition, currentReplaceMode,
    chainModeChecked, newColorInputValue, alphaSliderValue,
    boundaryThresholdValue, replaceBtn, onChainUpdate,
  } = ctx_;

  if (!selectedColor) {
    alert('先に画像上の色をクリックして選択してください。');
    return;
  }

  const newColorHex = newColorInputValue.trim();
  if (!/^#[0-9A-Fa-f]{6}$/.test(newColorHex)) {
    alert('正しい16進数カラーコード (#RRGGBB) を入力してください。');
    return;
  }

  const newColor = hexToRgb(newColorHex);
  const newAlpha = parseInt(alphaSliderValue);

  updateMessage('処理中...');
  replaceBtn.disabled = true;

  setTimeout(() => {
    let replacedCount: number;

    if (currentReplaceMode === 'pin') {
      if (!pinPosition) {
        alert('ピンモードではピンを配置してから置換してください。');
        replaceBtn.disabled = false;
        return;
      }
      removePinMarker(ctx);
      const threshold = parseInt(boundaryThresholdValue);
      replacedCount = floodFillReplace(ctx, canvas, pinPosition.x, pinPosition.y, selectedColor, newColor, newAlpha, threshold);
    } else {
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      replacedCount = 0;

      for (let i = 0; i < data.length; i += 4) {
        if (isSimilarColor(data[i], data[i + 1], data[i + 2], selectedColor, 5)) {
          data[i] = newColor.r;
          data[i + 1] = newColor.g;
          data[i + 2] = newColor.b;
          data[i + 3] = newAlpha;
          replacedCount++;
        }
      }

      ctx.putImageData(imageData, 0, 0);
    }

    if (chainModeChecked && replacedCount > 0) {
      onChainUpdate({ r: newColor.r, g: newColor.g, b: newColor.b, a: newAlpha });
    }

    updateMessage(`置換完了! ${replacedCount.toLocaleString()} ピクセルを置換しました。`);
    replaceBtn.disabled = false;

    if (replacedCount === 0) {
      alert('指定した色と類似するピクセルが見つかりませんでした。');
    }

    if (currentReplaceMode === 'pin' && pinPosition) {
      drawPinMarker(ctx, canvas, pinPosition.x, pinPosition.y, selectedColor);
    }
  }, 100);
}

export function makeTransparent(ctx_: Omit<ReplaceContext, 'newColorInputValue' | 'alphaSliderValue' | 'chainModeChecked' | 'onChainUpdate'> & { transparentBtn: HTMLButtonElement }): void {
  const {
    canvas, ctx, selectedColor, pinPosition, currentReplaceMode,
    boundaryThresholdValue, replaceBtn, transparentBtn,
  } = ctx_;

  if (!selectedColor) {
    alert('先に画像上の色をクリックして選択してください。');
    return;
  }

  updateMessage('処理中...');
  transparentBtn.disabled = true;

  setTimeout(() => {
    let replacedCount: number;

    if (currentReplaceMode === 'pin') {
      if (!pinPosition) {
        alert('ピンモードではピンを配置してから透過化してください。');
        transparentBtn.disabled = false;
        return;
      }
      removePinMarker(ctx);
      const threshold = parseInt(boundaryThresholdValue);
      replacedCount = floodFillTransparent(ctx, canvas, pinPosition.x, pinPosition.y, selectedColor, threshold);
    } else {
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      replacedCount = 0;

      for (let i = 0; i < data.length; i += 4) {
        if (isSimilarColor(data[i], data[i + 1], data[i + 2], selectedColor, 5)) {
          data[i + 3] = 0;
          replacedCount++;
        }
      }

      ctx.putImageData(imageData, 0, 0);
    }

    updateMessage(`透過化完了! ${replacedCount.toLocaleString()} ピクセルを透過にしました。`);
    transparentBtn.disabled = false;

    if (replacedCount === 0) {
      alert('指定した色と類似するピクセルが見つかりませんでした。');
    }

    if (currentReplaceMode === 'pin' && pinPosition) {
      drawPinMarker(ctx, canvas, pinPosition.x, pinPosition.y, selectedColor);
    }
  }, 100);
}

export async function copyToClipboard(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  pinPosition: PinPosition | null,
  currentReplaceMode: ReplaceMode,
  selectedColor: RgbaColor | null,
): Promise<void> {
  try {
    removePinMarker(ctx);
    canvas.toBlob(async (blob) => {
      if (!blob) {
        alert('画像のコピーに失敗しました。');
        return;
      }
      try {
        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
        updateMessage('画像をクリップボードにコピーしました!');
        if (currentReplaceMode === 'pin' && pinPosition) {
          drawPinMarker(ctx, canvas, pinPosition.x, pinPosition.y, selectedColor);
        }
      } catch (err) {
        console.error('クリップボードへのコピーに失敗:', err);
        alert('クリップボードへのコピーに失敗しました。ブラウザがこの機能をサポートしていない可能性があります。');
      }
    }, 'image/png');
  } catch (err) {
    console.error('エラー:', err);
    alert('画像のコピーに失敗しました。');
  }
}

export function downloadImage(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  pinPosition: PinPosition | null,
  currentReplaceMode: ReplaceMode,
  selectedColor: RgbaColor | null,
): void {
  removePinMarker(ctx);
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'replaced_image.png';
    a.click();
    URL.revokeObjectURL(url);
    updateMessage('画像をダウンロードしました!');
    if (currentReplaceMode === 'pin' && pinPosition) {
      drawPinMarker(ctx, canvas, pinPosition.x, pinPosition.y, selectedColor);
    }
  }, 'image/png');
}

export { rgbToHex };
