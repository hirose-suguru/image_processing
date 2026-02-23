import type { RgbaColor, PinPosition, ReplaceMode } from './types';
import { rgbToHex, hexToRgb } from './color';
import { drawPinMarker, removePinMarker, loadImageToCanvas } from './canvas';
import {
  updateMessage,
  updateModeIndicators,
  updatePinInfo,
  toggleSettingsPanel,
  initThresholdSlider,
} from './ui';
import { replaceColor, makeTransparent, copyToClipboard, downloadImage } from './replace';
import { render as renderHeader } from './components/header';
import { render as renderCanvasArea } from './components/canvasArea';
import { render as renderFooter } from './components/footer';
import { render as renderModePanel } from './components/modePanel';
import { render as renderSettingsPanel } from './components/settingsPanel';
import { render as renderColorPanel } from './components/colorPanel';
import { render as renderActionButtons } from './components/actionButtons';

// --- コンポーネントのレンダリング ---
document.getElementById('header')!.innerHTML = renderHeader();
document.getElementById('canvas-area')!.innerHTML = renderCanvasArea();
document.getElementById('footer')!.innerHTML = renderFooter();
document.getElementById('mode-panel')!.innerHTML = renderModePanel();
document.getElementById('settings-panel')!.innerHTML = renderSettingsPanel();
document.getElementById('color-panel')!.innerHTML = renderColorPanel();
document.getElementById('action-buttons')!.innerHTML = renderActionButtons();

// --- DOM要素 ---
const canvas = document.getElementById('canvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
const fileInput = document.getElementById('fileInput') as HTMLInputElement;
const placeholderText = document.getElementById('placeholderText') as HTMLSpanElement;
const selectedColorSample = document.getElementById('selectedColorSample') as HTMLDivElement;
const selectedColorHex = document.getElementById('selectedColorHex') as HTMLDivElement;
const selectedColorRgb = document.getElementById('selectedColorRgb') as HTMLDivElement;
const newColorInput = document.getElementById('newColorInput') as HTMLInputElement;
const colorPicker = document.getElementById('colorPicker') as HTMLInputElement;
const newColorSample = document.getElementById('newColorSample') as HTMLDivElement;
const newColorRgb = document.getElementById('newColorRgb') as HTMLDivElement;
const replaceBtn = document.getElementById('replaceBtn') as HTMLButtonElement;
const transparentBtn = document.getElementById('transparentBtn') as HTMLButtonElement;
const copyBtn = document.getElementById('copyBtn') as HTMLButtonElement;
const downloadBtn = document.getElementById('downloadBtn') as HTMLButtonElement;
const alphaSlider = document.getElementById('alphaSlider') as HTMLInputElement;
const alphaValue = document.getElementById('alphaValue') as HTMLDivElement;
const chainModeToggle = document.getElementById('chainModeToggle') as HTMLInputElement;
const boundaryThreshold = document.getElementById('boundaryThreshold') as HTMLInputElement;
const fileSelectBtn = document.getElementById('fileSelectBtn') as HTMLButtonElement;
const settingsToggleBtn = document.getElementById('settingsToggleBtn') as HTMLButtonElement;

// --- 状態 ---
let selectedColor: RgbaColor | null = null;
let pinPosition: PinPosition | null = null;
let currentReplaceMode: ReplaceMode = 'all';

// --- 初期化 ---
initThresholdSlider();
updateModeIndicators(currentReplaceMode, chainModeToggle.checked, pinPosition);

// --- ファイル選択 ---
fileSelectBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  loadImageToCanvas(file, canvas, ctx, (_img) => {
    placeholderText.style.display = 'none';
    canvas.style.display = 'block';
    canvas.classList.add('animate-fade-in');
    copyBtn.disabled = false;
    downloadBtn.disabled = false;
    updateMessage('画像上の任意の場所をクリックして、置換したい色を選択してください');
  });
});

// --- Canvasクリック: 色取得 ---
canvas.addEventListener('click', (event) => {
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const pixelX = Math.floor(x * scaleX);
  const pixelY = Math.floor(y * scaleY);

  removePinMarker(ctx);
  const imageData = ctx.getImageData(pixelX, pixelY, 1, 1);
  const data = imageData.data;
  const [r, g, b, a] = [data[0], data[1], data[2], data[3]];

  selectedColor = { r, g, b, a };

  const hexColor = rgbToHex(r, g, b);
  selectedColorSample.style.background = hexColor;
  selectedColorHex.textContent = hexColor;
  selectedColorRgb.textContent = `RGB(${r}, ${g}, ${b})`;

  replaceBtn.disabled = false;
  transparentBtn.disabled = false;

  if (currentReplaceMode === 'pin') {
    pinPosition = { x: pixelX, y: pixelY };
    updatePinInfo(`ピン位置: (${pixelX}, ${pixelY}) - 色: ${hexColor}`);
    drawPinMarker(ctx, canvas, pixelX, pixelY, selectedColor);
    updateModeIndicators(currentReplaceMode, chainModeToggle.checked, pinPosition);
  }
});

// --- カラープレビュー更新 ---
function updateColorPreview(): void {
  const hex = newColorInput.value.trim();
  if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
    const rgb = hexToRgb(hex);
    const alpha = parseInt(alphaSlider.value) / 255;
    newColorSample.style.background = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
    newColorRgb.textContent = `RGB(${rgb.r}, ${rgb.g}, ${rgb.b})`;
  }
}

colorPicker.addEventListener('input', () => {
  newColorInput.value = colorPicker.value.toUpperCase();
  updateColorPreview();
});

newColorInput.addEventListener('input', () => {
  const hex = newColorInput.value.trim();
  if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
    colorPicker.value = hex;
    updateColorPreview();
  }
});

alphaSlider.addEventListener('input', () => {
  const alpha = parseInt(alphaSlider.value);
  const percentage = Math.round((alpha / 255) * 100);
  if (alpha === 255) {
    alphaValue.textContent = '255 (不透明)';
  } else if (alpha === 0) {
    alphaValue.textContent = '0 (完全透明)';
  } else {
    alphaValue.textContent = `${alpha} (${percentage}%)`;
  }
  updateColorPreview();
});

// --- モードトグル ---
document.getElementById('pinModeToggle')!.addEventListener('click', () => {
  if (currentReplaceMode === 'pin') {
    currentReplaceMode = 'all';
    pinPosition = null;
    removePinMarker(ctx);
    updatePinInfo('ピン未配置');
  } else {
    currentReplaceMode = 'pin';
  }
  updateModeIndicators(currentReplaceMode, chainModeToggle.checked, pinPosition);
});

document.getElementById('chainModeToggle_div')!.addEventListener('click', () => {
  chainModeToggle.checked = !chainModeToggle.checked;
  updateModeIndicators(currentReplaceMode, chainModeToggle.checked, pinPosition);
});

settingsToggleBtn.addEventListener('click', toggleSettingsPanel);

// --- ボタン ---
replaceBtn.addEventListener('click', () => {
  replaceColor({
    canvas,
    ctx,
    selectedColor,
    pinPosition,
    currentReplaceMode,
    chainModeChecked: chainModeToggle.checked,
    newColorInputValue: newColorInput.value,
    alphaSliderValue: alphaSlider.value,
    boundaryThresholdValue: boundaryThreshold.value,
    replaceBtn,
    transparentBtn,
    onChainUpdate: (newColor) => {
      selectedColor = newColor;
      const hexColor = rgbToHex(newColor.r, newColor.g, newColor.b);
      selectedColorSample.style.background = hexColor;
      selectedColorHex.textContent = hexColor;
      selectedColorRgb.textContent = `RGB(${newColor.r}, ${newColor.g}, ${newColor.b})`;
    },
  });
});

transparentBtn.addEventListener('click', () => {
  makeTransparent({
    canvas,
    ctx,
    selectedColor,
    pinPosition,
    currentReplaceMode,
    boundaryThresholdValue: boundaryThreshold.value,
    replaceBtn,
    transparentBtn,
  });
});

copyBtn.addEventListener('click', () => {
  copyToClipboard(ctx, canvas, pinPosition, currentReplaceMode, selectedColor);
});

downloadBtn.addEventListener('click', () => {
  downloadImage(ctx, canvas, pinPosition, currentReplaceMode, selectedColor);
});
