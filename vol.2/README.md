# Vol.2 - HTTP/3実装

シンプルなHTTP/3クライアント・サーバーの実装例です。

## セットアップ

プロジェクトルート（Seminarディレクトリ）で以下を実行：

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

### 期待される出力

```
Status: 200 OK
Protocol: HTTP/3.0
Response:
Hello HTTP/3!
Protocol: HTTP/3.0
```

## 実装の特徴

- **サーバー**: HTTP/3サーバー（ポート12345、UDP）
- **クライアント**: HTTP/3クライアント
- **証明書**: 自己署名証明書をメモリ上で自動生成（ファイル不要）


## 注意事項

- HTTP/3はQUICプロトコル（UDP）上で動作し、TLS暗号化が必須です
- `InsecureSkipVerify`を使用しているため、開発環境専用です
- 本番環境では適切な証明書検証が必要です