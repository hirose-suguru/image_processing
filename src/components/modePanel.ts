export function render(): string {
  return `
    <div class="bg-white rounded-xl border-2 border-slate-400 p-6 space-y-2" style="padding-top: 14px; padding-bottom: 14px">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">モード設定</h2>
        <button id="settingsToggleBtn"
                class="p-1.5 rounded-lg hover:bg-slate-100 transition-colors border border-slate-300"
                title="詳細設定">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" y1="6" x2="20" y2="6"/>
            <line x1="4" y1="12" x2="20" y2="12"/>
            <line x1="4" y1="18" x2="20" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="flex items-center gap-3 cursor-pointer" id="pinModeToggle">
        <svg id="pinModeIndicator" class="flex-shrink-0" width="18" height="18" viewBox="0 0 18 18">
          <circle cx="9" cy="9" r="7.5" fill="white" stroke="#1e293b" stroke-width="2"/>
        </svg>
        <span class="text-slate-700" style="font-size: 1rem;">ピンモード</span>
        <span class="text-xs text-slate-400 ml-auto" id="pinModeStatus"></span>
      </div>
      <div class="flex items-center gap-3 cursor-pointer" id="chainModeToggle_div">
        <svg id="chainModeIndicator" class="flex-shrink-0" width="18" height="18" viewBox="0 0 18 18">
          <circle cx="9" cy="9" r="7.5" fill="white" stroke="#1e293b" stroke-width="2"/>
        </svg>
        <span class="text-slate-700" style="font-size: 1rem;">連鎖モード</span>
      </div>
    </div>
  `;
}
