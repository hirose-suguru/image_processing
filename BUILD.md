# Tailwind CSS ビルド手順

## 前提条件
- Node.js がインストールされていること

## 初回セットアップ

```bash
# 依存関係のインストール
npm install
```

## ビルドコマンド

```bash
# CSSをビルド（本番用、圧縮あり）
npm run build
```

### 内部で実行されるコマンド
```bash
tailwindcss -i ./src/input.css -o ./dist/output.css --minify
```

| オプション | 説明 |
|-----------|------|
| `-i ./src/input.css` | 入力ファイル（Tailwindディレクティブ + カスタムCSS） |
| `-o ./dist/output.css` | 出力ファイル（ビルド成果物） |
| `--minify` | 圧縮（空白・改行削除） |

## 開発時（ウォッチモード）

CSSを変更するたびに自動でビルドしたい場合：

```bash
npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch
```

## ファイル構成

```
project/
├── src/
│   └── input.css       # 編集するファイル
├── dist/
│   └── output.css      # ビルド成果物（index.htmlが読み込む）
├── package.json
└── index.html
```

## CSSを編集したい場合

1. `src/input.css` を編集
2. `npm run build` を実行
3. `dist/output.css` が更新される
