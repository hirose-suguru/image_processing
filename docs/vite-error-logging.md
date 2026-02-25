# Viteプラグインによるエラーログ書き込みの仕組み

## 「ローカルにソースコードがあるのになぜデバッグが難しいのか」

### ブラウザとNode.jsは別の実行環境

Webアプリの開発では、コードが動く場所が2か所ある。

```
[あなたのPC（Node.js）]          [ブラウザ]
  - vite dev サーバーが起動        - HTMLを描画
  - TypeScriptをビルド             - JavaScriptを実行
  - ファイルの変更を監視           - ユーザー操作を処理
```

`vite dev` を実行すると Node.js がローカルサーバーとして起動し、TypeScript をコンパイルしてブラウザに届ける。
ブラウザはその成果物（JavaScript）を受け取って動かすだけ。

つまり**エラーが起きる場所**が2か所ある：

| エラーの種類 | 発生場所 | 確認できる場所 |
|---|---|---|
| TypeScriptの型エラー・構文エラー | Node.js（Vite） | **ターミナル** |
| 実行時エラー（undefinedアクセスなど） | ブラウザ | **ブラウザのDevTools（F12）** |

「ローカルにコードがある」のにブラウザのDevToolsを開かないとエラーがわからない理由はこれ。
ブラウザとNode.jsはプロセスが完全に別で、ブラウザのコンソールはターミナルには出ない。

---

## Viteプラグインとは

Viteのビルド・開発サーバーの動作を拡張する仕組み。
`vite.config.ts` の `plugins` 配列にオブジェクトを追加するだけで使える。

```ts
// vite.config.ts の基本形
export default defineConfig({
  plugins: [
    {
      name: 'my-plugin',       // プラグインの名前（デバッグ用）
      configureServer(server) { // dev サーバーが起動するときに呼ばれる
        // ここでサーバーをカスタマイズできる
      },
    }
  ]
});
```

プラグインが使えるフック（タイミング）の例：

| フック名 | 呼ばれるタイミング |
|---|---|
| `configureServer` | devサーバー起動時（WebSocketサーバーにアクセスできる） |
| `buildStart` | ビルド開始時 |
| `transform` | ファイルをトランスフォーム（コンパイル）するとき |
| `handleHotUpdate` | ファイルが変更されてHMRが走るとき |

---

## 今回実装するエラーログの仕組み

### サーバーサイドエラー（Node.js → ファイル）

Viteサーバーには `server.ws`（WebSocket）と `server.config.logger` がある。
`server.ws.on('error', ...)` や `vite:error` イベントをフックして、
`fs.appendFileSync` でファイルに書き込む。

```
[Vite dev server]
  ↓ ビルドエラー・HMRエラー検知
  ↓ fs.appendFileSync
[logs/error.log]
```

### ブラウザサイドエラー（ブラウザ → WebSocket → ファイル）

ブラウザのエラーはそのままではNode.js側に届かない。
そこで：
1. プラグインのクライアントコードとして `window.onerror` / `window.onunhandledrejection` を仕込む
2. エラーが起きたらブラウザからVite WebSocket経由でNode.jsにメッセージを送る
3. Node.js側で受け取ってファイルに書き込む

```
[ブラウザ]
  ↓ window.onerror でエラーキャッチ
  ↓ __vite_plugin_client__.send('browser-error', {...})
[Vite WebSocket]
  ↓ server.ws.on('browser-error', handler)
[Node.js]
  ↓ fs.appendFileSync
[logs/error.log]
```

### ログの保存先

```
image_processing/
  logs/
    error.log   ← サーバーとブラウザ両方のエラーがここに記録される
```

---

## 使い方

1. `npm run dev` でViteサーバーを起動
2. TypeScriptエラーやブラウザのランタイムエラーが発生すると `logs/error.log` に自動で追記される
3. ログは以下の形式で記録される：

```
[2024-01-01T12:00:00.000Z] [SERVER] ビルドエラーのメッセージ
[2024-01-01T12:00:01.000Z] [BROWSER] TypeError: Cannot read properties of undefined
  at main.ts:42:5
```
