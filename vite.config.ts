import { defineConfig, type Plugin } from 'vite';
import fs from 'fs';
import path from 'path';

function errorLoggerPlugin(): Plugin {
  const logFile = path.resolve(__dirname, 'logs/error.log');

  function writeLog(level: 'SERVER' | 'BROWSER', message: string): void {
    const timestamp = new Date().toISOString();
    const line = `[${timestamp}] [${level}] ${message}\n`;
    fs.mkdirSync(path.dirname(logFile), { recursive: true });
    fs.appendFileSync(logFile, line, 'utf-8');
  }

  return {
    name: 'error-logger',

    // サーバーサイドエラー（ビルドエラーなど）をキャッチ
    configureServer(server) {
      server.ws.on('error', (err) => {
        writeLog('SERVER', `WebSocket error: ${err.message}`);
      });

      // ブラウザからのエラーメッセージを受信
      server.ws.on('browser-error', (data: { message: string; stack?: string; source?: string }) => {
        const detail = data.stack
          ? `${data.message}\n  ${data.stack.split('\n').join('\n  ')}`
          : data.message;
        writeLog('BROWSER', detail);
      });
    },

    // ビルドエラーをキャッチ
    buildEnd(err) {
      if (err) {
        writeLog('SERVER', `Build error: ${err.message}`);
      }
    },

    // ブラウザに注入するクライアントコード
    // window.onerror / unhandledrejection をフックしてWebSocket経由で送信する
    transformIndexHtml() {
      return [
        {
          tag: 'script',
          attrs: { type: 'module' },
          children: `
if (import.meta.hot) {
  window.addEventListener('error', (event) => {
    import.meta.hot.send('browser-error', {
      message: event.message || String(event.error),
      stack: event.error?.stack ?? '',
      source: event.filename ? event.filename + ':' + event.lineno + ':' + event.colno : '',
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    const err = event.reason;
    import.meta.hot.send('browser-error', {
      message: err instanceof Error ? err.message : String(err),
      stack: err instanceof Error ? (err.stack ?? '') : '',
    });
  });
}
          `.trim(),
          injectTo: 'head-prepend',
        },
      ];
    },
  };
}

export default defineConfig({
  plugins: [errorLoggerPlugin()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
