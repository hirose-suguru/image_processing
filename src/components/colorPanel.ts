export function render(): string {
  return `
    <div class="bg-white rounded-xl border-2 border-slate-400 p-6 space-y-2" style="padding-top: 14px;">
      <h2 class="text-lg font-semibold text-slate-900" style="margin-bottom: 10px;">カラー設定</h2>

      <!-- クリックした色（置換元）-->
      <div class="space-y-4" style="margin-bottom: 20px;">
        <label class="text-sm font-medium text-slate-700" style="display: block; margin-bottom: 10px;">クリックした色</label>
        <div class="flex items-center gap-3">
          <div class="w-16 h-16 rounded-lg border-2 border-slate-300 flex-shrink-0"
               id="selectedColorSample" style="background: #ffffff;"></div>
          <div class="space-y-1 flex-1">
            <div class="font-mono text-sm bg-slate-50 px-3 py-2 rounded border border-slate-200"
                 id="selectedColorHex">#000000</div>
            <div class="font-mono text-sm text-slate-500 px-3" id="selectedColorRgb">RGB(0, 0, 0)</div>
          </div>
        </div>
      </div>

      <!-- 区切り線 -->
      <div class="border-b border-slate-300" style="margin-left: 10px; margin-right: 10px; margin-bottom: 15px;"></div>

      <!-- 新しい色（置換先）-->
      <div class="space-y-2">
        <label class="text-sm font-medium text-slate-700" style="display: block; margin-bottom: 20px;">新しい色</label>
        <div class="flex items-center gap-3">
          <input type="color" id="colorPicker" value="#FF0000"
                 class="w-16 h-16 rounded-lg border-2 border-slate-300 cursor-pointer">
          <div class="space-y-1 flex-1">
            <input type="text" id="newColorInput" placeholder="#FF0000" value="#FF0000" maxlength="7"
                   class="w-full font-mono text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all duration-300">
            <div class="font-mono text-sm text-slate-500 px-3" id="newColorRgb">RGB(255, 0, 0)</div>
          </div>
        </div>
      </div>

      <!-- 透過性 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-slate-700" style="display: block; margin-bottom: 10px;">透過性</label>
        <input type="range" id="alphaSlider" min="0" max="255" value="255"
               class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
               style="accent-color: rgba(0, 135, 196, 0.7);">
        <div class="font-mono text-xs text-slate-600 text-center bg-slate-50 px-3 py-2 rounded"
             id="alphaValue">255 (不透明)</div>
        <!-- 新しい色＋透過度のプレビュー -->
        <div class="w-full h-10 rounded-lg border-slate-300 checkerboard-bg"
             id="newColorSample" style="background: #FF0000; border-width: 3px;"></div>
      </div>
    </div>
  `;
}
