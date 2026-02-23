export function render(): string {
  return `
    <div id="settingsPanel" class="bg-white rounded-xl border-2 border-slate-400 p-6 space-y-4" style="display: none;">
      <h3 class="text-sm font-semibold text-slate-900">詳細設定</h3>
      <div class="space-y-2">
        <p class="text-xs font-medium text-slate-700">ピンモード</p>
        <p class="text-xs text-slate-500">画像上をクリックしてピンを配置。ピンから連結した同色領域のみ置換されます。</p>
        <div class="flex items-center gap-2">
          <span class="text-xs text-slate-700">境界しきい値:</span>
          <input type="range" id="boundaryThreshold" min="10" max="100" value="30"
                 class="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                 style="accent-color: rgba(0, 135, 196, 0.7);">
          <span class="text-xs font-mono text-slate-600" id="thresholdValue">30</span>
        </div>
        <div id="pinInfo" class="text-xs text-slate-500">ピン未配置</div>
      </div>
      <div class="border-b border-slate-200"></div>
      <div class="space-y-2">
        <p class="text-xs font-medium text-slate-700">連鎖変換モード</p>
        <p class="text-xs text-slate-500">ONの場合、置換後に「クリックした色」が自動的に新しい色に更新されます</p>
      </div>
    </div>
  `;
}
