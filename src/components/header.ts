export function render(): string {
  return `
    <header class="border-b border-slate-300 flex items-center gap-4 flex-wrap justify-between" style="padding-bottom: 10px;">
      <div class="flex items-center gap-4 flex-wrap">
        <h1 class="font-semibold text-slate-900"
            style="font-family: 'M PLUS Rounded 1c', sans-serif; font-size: 1.60rem;">
          カラーコード検索・置換ツール
        </h1>
        <label class="px-6 py-2.5 text-white rounded-lg font-medium transition-all duration-300 ease-out hover:brightness-110 hover:shadow-lg hover:-translate-y-0.5 active:scale-[0.98] cursor-pointer"
               style="background-color: rgba(195, 135, 1, 0.5); font-size: 1rem; text-shadow: 0 1px 1.5px rgba(0, 0, 0, 0.15);">
          画像ファイルを選択
          <input type="file" id="fileInput" accept="image/png, image/jpeg, image/jpg" class="hidden">
        </label>
      </div>
      <p class="text-slate-600 text-sm bg-slate-50 px-3 py-2 rounded border border-slate-200 max-w-xs" id="infoMessage"></p>
    </header>
  `;
}
