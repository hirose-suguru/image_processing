import type { PinPosition, ReplaceMode } from './types';

const infoMessage = document.getElementById('infoMessage') as HTMLParagraphElement;
const pinModeIndicator = document.getElementById('pinModeIndicator') as unknown as SVGSVGElement;
const chainModeIndicator = document.getElementById('chainModeIndicator') as unknown as SVGSVGElement;
const pinModeStatus = document.getElementById('pinModeStatus') as HTMLSpanElement;
const pinInfo = document.getElementById('pinInfo') as HTMLDivElement;
const thresholdValue = document.getElementById('thresholdValue') as HTMLSpanElement;
const settingsPanel = document.getElementById('settingsPanel') as HTMLDivElement;

export function updateMessage(text: string): void {
  infoMessage.classList.remove('animate-slide-up');
  infoMessage.textContent = text;
  setTimeout(() => {
    infoMessage.classList.add('animate-slide-up');
  }, 10);
}

export function updateModeIndicators(
  currentReplaceMode: ReplaceMode,
  chainModeChecked: boolean,
  pinPosition: PinPosition | null,
): void {
  const pinCircle = pinModeIndicator.querySelector('circle')!;
  const chainCircle = chainModeIndicator.querySelector('circle')!;

  pinCircle.setAttribute('fill', currentReplaceMode === 'pin' ? 'rgba(0, 135, 196, 0.7)' : 'white');
  chainCircle.setAttribute('fill', chainModeChecked ? 'rgba(0, 135, 196, 0.7)' : 'white');
  pinModeStatus.textContent = pinPosition ? `(${pinPosition.x}, ${pinPosition.y})` : '';

  updateModeMessage(currentReplaceMode, chainModeChecked);
}

export function updateModeMessage(currentReplaceMode: ReplaceMode, chainModeChecked: boolean): void {
  const messages: string[] = [];
  if (currentReplaceMode === 'pin') messages.push('ピンモード ON');
  if (chainModeChecked) messages.push('連鎖モード ON');

  if (messages.length > 0) {
    infoMessage.textContent = messages.join(' / ');
    infoMessage.style.display = '';
  } else {
    infoMessage.textContent = '';
    infoMessage.style.display = 'none';
  }
}

export function updatePinInfo(text: string): void {
  pinInfo.textContent = text;
}

export function toggleSettingsPanel(): void {
  settingsPanel.style.display = settingsPanel.style.display === 'none' ? 'block' : 'none';
}

export function initThresholdSlider(): void {
  const boundaryThreshold = document.getElementById('boundaryThreshold') as HTMLInputElement;
  boundaryThreshold.addEventListener('input', () => {
    thresholdValue.textContent = boundaryThreshold.value;
  });
}
