# 画像カラー置換ツール - Web公開準備計画

## 概要
index.htmlをVercelで公開するための準備として、以下を実施する。

## 作業内容

### 1. Tailwind CSSビルド環境の構築
**目的**: CDN版から本番用ビルド版に移行し、パフォーマンス向上

**手順**:
1. `package.json`を作成（npm init）
2. Tailwind CSSをインストール（npm install）
3. `tailwind.config.js`を作成（設定ファイル）
4. `src/input.css`を作成（Tailwindディレクティブを記述）
5. ビルドコマンドを実行 → `dist/output.css`生成
6. index.htmlを修正（CDNスクリプト → ビルド済みCSS読み込み）

**ファイル構成（ビルド後）**:
```
広瀬傑_関係/
├── index.html          # 修正
├── package.json        # 新規
├── tailwind.config.js  # 新規
├── src/
│   └── input.css       # 新規（Tailwind入力）
└── dist/
    └── output.css      # 生成（ビルド成果物）
```

### 2. メタデータの追加
**対象ファイル**: index.html

- `<meta name="description">` - 検索エンジン用説明文
- OGPタグ一式 - SNS共有時のカード表示用
  - `og:title`
  - `og:description`
  - `og:type`
  - `og:url`（Vercel公開後に設定）
  - `og:image`（後で追加予定、今回はスキップ）
- Twitter Card用タグ

### 3. Faviconの設定
**対象ファイル**: index.html

- シンプルなSVG形式のfaviconを新規作成（パレットアイコンなど）
- `<link rel="icon">` タグを追加
- SVGならデザインツール不要でコードで作成可能

### 4. Vercelデプロイ準備
- 必要に応じて`.gitignore`作成（node_modules除外）
- Vercelへのデプロイ手順を説明

## 修正対象ファイル
- `C:\Users\tnkko\Documents\広瀬傑_関係\index.html`

## 新規作成ファイル
- `package.json`
- `tailwind.config.js`
- `src/input.css`
- `dist/output.css`（ビルドで自動生成）

## 検証方法
1. `npm run build` でTailwindビルドが成功すること
2. ローカルでindex.htmlを開き、スタイルが正しく適用されていること
3. Vercelにデプロイ後、HTTPS経由でアクセスできること
4. クリップボードコピー機能が動作すること（HTTPS必須）
