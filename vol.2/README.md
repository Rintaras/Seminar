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

## 注意事項

- サーバーを実行するには、TLS証明書（`server.crt`と`server.key`）が必要です
- デフォルトポートは`12345`です