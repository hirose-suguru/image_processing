# アーキテクチャ概要

## プロジェクトの目的

PNG / JPEG 画像をブラウザ上で読み込み、特定の色を別の色に置換したり透過にしたりできるWebツール。
サーバーへの通信は一切なく、すべての処理がブラウザ内で完結する。

---

## ディレクトリ構成

```
image_processing/
├── index.html              # エントリーポイント。div#id でマウント先を定義
├── vite.config.ts          # Viteビルド設定 + エラーログプラグイン
├── tsconfig.json           # src/ 向けのTypeScript設定
├── tsconfig.node.json      # vite.config.ts 向けのTypeScript設定（Node.js型が必要）
├── package.json
│
├── src/                    # アプリケーションソースコード
│   ├── main.ts             # エントリーポイント。状態管理・イベント配線
│   ├── types.ts            # 型定義（RgbaColor, PinPosition, ReplaceMode）
│   ├── color.ts            # 色変換ユーティリティ（RGB↔HEX, 色類似判定）
│   ├── canvas.ts           # Canvas操作（画像読み込み、ピンマーカー描画）
│   ├── ui.ts               # UI更新関数（メッセージ表示、モード表示、スライダー）
│   ├── replace.ts          # 色置換・透過化・コピー・ダウンロードのロジック
│   ├── floodFill.ts        # 塗りつぶし（フラッドフィル）アルゴリズム
│   ├── input.css           # Tailwind CSS のエントリーファイル
│   └── components/         # HTML文字列を返すレンダリング関数群
│       ├── header.ts       # タイトル・ファイル選択ボタン
│       ├── canvasArea.ts   # 画像表示Canvas
│       ├── footer.ts       # 作者情報フッター
│       ├── modePanel.ts    # ピンモード・連鎖モード切替、設定ボタン
│       ├── settingsPanel.ts # 詳細設定（境界しきい値スライダー、ピン情報）
│       ├── colorPanel.ts   # 色選択パネル（選択色・新しい色・アルファ値）
│       └── actionButtons.ts # 実行ボタン（置換・透過化・コピー・DL）
│
├── public/                 # Viteが静的ファイルとしてそのまま配信するディレクトリ
│   ├── favicon.svg         # ファビコン
│   ├── icon_1.jpg          # フッターのプロフィール画像
│   └── output.css          # Tailwindがビルドして生成したCSS（src/input.css → ここ）
│
├── dist/                   # `npm run build` で生成されるビルド成果物（.gitignore済み）
│   ├── index.html          # 最適化済みHTML
│   ├── assets/index-xxx.js # バンドル・最小化済みJS
│   ├── favicon.svg
│   ├── icon_1.jpg
│   └── output.css
│
├── docs/                   # 技術解説ドキュメント
│   ├── js-modularization.md
│   └── vite-error-logging.md
│
├── plans/                  # 設計・アーキテクチャドキュメント（このファイルなど）
│   └── architecture.md
│
└── logs/                   # エラーログ出力先（.gitignore済み、開発時のみ生成）
    └── error.log
```

---

## dist/ とは何か

`npm run build` を実行したときに Vite が生成するフォルダ。

| 操作 | 使うもの |
|---|---|
| 開発中（`npm run dev`） | `src/` のコードを直接Viteが変換してブラウザに届ける。`dist/` は使わない |
| 本番デプロイ（`npm run build`） | TypeScriptをコンパイル・バンドル・minifyして `dist/` に出力。これをサーバーに置く |

`dist/` の中身はソースコードから自動生成できるので、Gitで管理する必要がなく `.gitignore` に入れてある。

---

## 処理の全体フロー

```
[ユーザー操作]
      |
      ↓
[main.ts]  ← すべてのイベントリスナーと状態（selectedColor, pinPosition, currentReplaceMode）を管理
      |
      ├── ファイル選択 → canvas.ts: loadImageToCanvas()  → Canvasに描画
      |
      ├── Canvas クリック → ctx.getImageData() でピクセル色を取得
      |                    → ピンモードなら canvas.ts: drawPinMarker()
      |
      ├── 置換ボタン → replace.ts: replaceColor()
      |                    ├── allモード: 全ピクセルをループしてcolor.ts: isSimilarColor()で判定・置換
      |                    └── pinモード: floodFill.ts: floodFillReplace()（BFS塗りつぶし）
      |
      ├── 透過ボタン → replace.ts: makeTransparent()
      |                    ├── allモード: 全ピクセルのアルファ値を0に
      |                    └── pinモード: floodFill.ts: floodFillTransparent()
      |
      ├── コピーボタン → replace.ts: copyToClipboard() → canvas.toBlob() → Clipboard API
      |
      └── DLボタン   → replace.ts: downloadImage() → canvas.toBlob() → <a>タグでDL
```

---

## コンポーネントの仕組み

`src/components/` の各ファイルは `render(): string` という関数を1つだけエクスポートする。
HTML文字列を返すだけで、フレームワーク（React等）は使っていない。

`main.ts` 起動時に一度だけ呼ばれ、`index.html` の各 `div` に `.innerHTML` で差し込む：

```ts
document.getElementById('header')!.innerHTML = renderHeader();
document.getElementById('mode-panel')!.innerHTML = renderModePanel();
// ...
```

その後 `main.ts` が `getElementById` で各要素を取得し、イベントリスナーを登録する。
`ui.ts` の各関数も必要なタイミングで `getElementById` を呼ぶ（モジュールロード時ではなく関数呼び出し時）。

---

## 置換モードの説明

| モード | 動作 |
|---|---|
| **all モード**（デフォルト） | 画像全体をスキャンして、選択色と類似（差分が各チャンネル±5以内）するピクセルをすべて置換 |
| **pin モード** | クリックした座標を起点にフラッドフィル（BFS）で連結した同色領域だけを置換。境界しきい値（色距離）で拡張範囲を制御 |
| **連鎖モード** | 置換後、「選択色」が自動的に「新しい色」に更新される。同じ操作を繰り返すと段階的に色を変えていける |

---

## 開発ツールチェーン

| ツール | 役割 |
|---|---|
| **Vite** | 開発サーバー + TypeScriptトランスパイル + バンドル |
| **TypeScript** | 型安全なJS。`tsconfig.json` の `"moduleResolution": "bundler"` でViteとの相性を最適化 |
| **Tailwind CSS v4** | ユーティリティCSSフレームワーク。`src/input.css` → `public/output.css` にビルド |
| **@types/node** | `vite.config.ts` 内で `fs`, `path`, `__dirname` を使うための型定義 |

### CSS の注意点

Tailwind は **実際にファイル内に書かれているクラス名だけ** をスキャンしてCSSを生成する。
`src/components/*.ts` の中にTailwindクラスを追加したら `npm run css:build`（または `css:watch`）で再ビルドが必要。
再ビルドしないと新しいクラスがCSSに出力されず、スタイルが当たらないバグになる。

---

## エラーロギング（開発時のみ）

`vite.config.ts` のカスタムプラグインが有効な間、エラーは `logs/error.log` に記録される。

- **サーバーサイドエラー**: Vite WebSocketエラー・ビルドエラー → 直接ファイルに書き込み
- **ブラウザサイドエラー**: `window.onerror` / `unhandledrejection` → WebSocket → Node.js → ファイルに書き込み

詳細は `docs/vite-error-logging.md` を参照。
