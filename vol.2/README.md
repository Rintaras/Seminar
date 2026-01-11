# Vol.2 - HTTP/2 & HTTP/3実装

HTTP/2とHTTP/3のシンプルなクライアント・サーバー実装例です。

## プロジェクト構成

```
vol.2/
├── cert/              # 共通証明書モジュール
│   ├── cert.go       # 証明書生成・管理
│   ├── cert.crt      # 自動生成される証明書（gitignore）
│   └── cert.key      # 自動生成される秘密鍵（gitignore）
├── HTTP2/            # HTTP/2実装
│   ├── server/       # HTTP/2サーバー（ポート2000）
│   │   └── main.go
│   └── client/       # HTTP/2クライアント
│       └── main.go
└── HTTP3/            # HTTP/3実装
    ├── server/       # HTTP/3サーバー（ポート3000）
    │   └── main.go
    └── client/       # HTTP/3クライアント
        └── main.go
```

## セットアップ

プロジェクトルート（Seminarディレクトリ）で以下を実行：

### 1. Goモジュールの初期化（初回のみ）

```bash
go mod init seminar
```

### 2. 必要なパッケージのインストール

```bash
go get github.com/quic-go/quic-go
go get golang.org/x/net/http2
```

## 実行方法

**注意**: `go build`ではなく`go run`を使用してください。バイナリファイルが生成されず、ディレクトリが見やすくなります。

### HTTP/2サーバー＆クライアント

#### サーバーの起動（ポート2000）
```bash
cd vol.2/HTTP2/server
go run main.go
```

#### クライアントの実行
別のターミナルで：
```bash
cd vol.2/HTTP2/client
go run main.go
```

#### 期待される出力
```
Status: 200 OK
Protocol: HTTP/2.0
Response:
Hello HTTP/2!
Protocol: HTTP/2.0
```

### HTTP/3サーバー＆クライアント

#### サーバーの起動（ポート3000）
```bash
cd vol.2/HTTP3/server
go run main.go
```

#### クライアントの実行
別のターミナルで：
```bash
cd vol.2/HTTP3/client
go run main.go
```

#### 期待される出力
```
Status: 200 OK
Protocol: HTTP/3.0
Response:
Hello HTTP/3!
Protocol: HTTP/3.0
```

## HTTP/2とHTTP/3の違い

| 項目 | HTTP/2 | HTTP/3 |
|-----|--------|--------|
| **トランスポート** | TCP | UDP (QUIC) |
| **ポート** | 2000 | 3000 |
| **多重化** | TCPストリーム | QUICストリーム |
| **ヘッドオブライン<br>ブロッキング** | あり | なし |
| **接続確立** | TCP + TLS | QUIC (統合) |

## 証明書について

### 自動生成
- 初回起動時に`vol.2/cert/`に自己署名証明書を自動生成
- 2回目以降は既存の証明書を再利用
- PEM形式で保存

### ファイル
- `cert.crt` - 証明書（RSA 2048bit）
- `cert.key` - 秘密鍵（パーミッション0600）

### セキュリティ
- **開発環境専用**: `InsecureSkipVerify`を使用
- **本番環境**: 適切な証明書と証明書検証が必要

## 注意事項

- HTTP/2: TCP上で動作、HTTP/1.1フォールバックあり
- HTTP/3: QUIC（UDP）上で動作、TLS 1.3必須
- 両方のサーバーは同時起動可能（異なるポート）
- 証明書は両サーバーで共有