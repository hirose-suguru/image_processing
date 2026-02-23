export function render(): string {
  return `
    <div class="flex gap-2">
      <button id="replaceBtn" disabled
              class="flex-1 px-2 py-2.5 text-white rounded-lg font-medium transition-all duration-300 ease-out hover:opacity-90 hover:shadow-lg active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none disabled:hover:scale-100"
              style="background-color: rgba(0, 135, 196, 0.7); font-size: 1rem; text-shadow: 0 1px 1.5px rgba(0, 0, 0, 0.15);">
        カラー置換
      </button>
      <button id="transparentBtn" disabled
              class="flex-1 px-2 py-2.5 text-white rounded-lg font-medium transition-all duration-300 ease-out hover:opacity-90 hover:shadow-lg active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none disabled:hover:scale-100"
              style="background-color: rgba(139, 92, 246, 0.7); font-size: 1rem; text-shadow: 0 1px 1.5px rgba(0, 0, 0, 0.15);">
        透過化
      </button>
      <button id="copyBtn" disabled
              class="flex-1 px-2 py-2.5 border border-slate-400 text-slate-700 rounded-lg font-medium transition-all duration-300 hover:bg-slate-50 hover:border-slate-500 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:scale-100"
              style="font-size: 1rem;">
        コピー
      </button>
      <button id="downloadBtn" disabled
              class="flex-1 px-2 py-2.5 border border-slate-400 text-slate-700 rounded-lg font-medium transition-all duration-300 hover:bg-slate-50 hover:border-slate-500 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:scale-100"
              style="font-size: 1rem;">
        ダウンロード
      </button>
    </div>
  `;
}
