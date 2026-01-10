# Vol.2 - HTTP3/QUIC実装

## セットアップ

以下のコマンドは**Seminarディレクトリ**（プロジェクトルート）で実行してください。

### 1. Goモジュールの初期化

```bash
go mod init seminar
```

### 2. quic-goパッケージのインストール

```bash
go get github.com/quic-go/quic-go
```

## 実行方法

### サーバーの起動

```bash
cd vol.2/HTTP3/server
go run main.go
```

### クライアントの実行

別のターミナルで以下を実行：

```bash
cd vol.2/HTTP3/client
go run main.go
```

## ブラウザでのアクセス

サーバー起動後、ブラウザで以下のURLにアクセスできます：

### HTTP/3で接続（推奨）

```
https://localhost:12345/
```

このポートはHTTP/3（UDP）専用です。

**ChromeでHTTP/3を確実に使用する方法:**

#### 方法1: Chromeフラグを有効化

1. Chromeで `chrome://flags/#enable-quic` を開く
2. `Experimental QUIC protocol` を **Enabled** に設定
3. Chromeを再起動
4. `https://localhost:12345/` にアクセス

#### 方法2: コマンドラインでChromeを起動

```bash
cd vol.2/HTTP3
./start-chrome-http3.sh
```

このスクリプトがHTTP/3を強制的に有効化してChromeを起動します。

### HTTP/2で接続（フォールバック）

```
https://localhost:12346/
```

このポートはHTTP/2（TCP）フォールバックです。

**注意**: 
- 自己署名証明書を使用しているため、ブラウザに警告が表示されます
- 「詳細設定」→「安全でないサイトに進む」で接続してください
- ページには接続に使用されたプロトコルが表示されます
- **Goクライアント（推奨）**: 最も確実にHTTP/3を確認できます

## 注意事項

- HTTP/3はQUICプロトコル上で動作し、必ずTLS暗号化を使用します
- サーバーは起動時にメモリ上で自己署名証明書を自動生成します（証明書ファイル不要）
- クライアントは`InsecureSkipVerify`を使用しているため、開発環境専用です
- ポート12345: HTTP/3専用（UDP）
- ポート12346: HTTP/2フォールバック（TCP）