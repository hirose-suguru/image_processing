export function render(): string {
  return `
    <div class="border-2 border-dashed border-slate-200 rounded-xl min-h-[500px] flex items-center justify-center bg-slate-50 overflow-auto p-8">
      <span class="text-slate-400 text-lg" id="placeholderText">画像を選択してください</span>
      <canvas id="canvas" class="max-w-full max-h-[600px] cursor-crosshair hidden"></canvas>
    </div>
  `;
}
