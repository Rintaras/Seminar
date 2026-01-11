# Seminar - HTTPプロトコル実装

HTTP/1.1、HTTP/2、HTTP/3の実装例とGoプログラミングの学習プロジェクトです。

## プロジェクト構成

```
Seminar/
├── Vol.1/              # 基礎実装
│   ├── HTTP1.1/       # HTTP/1.1サーバー
│   ├── HTTP2/         # HTTP/2サーバー（単一ファイル）
│   ├── Sum/           # 基本的なGoプログラム
│   └── intro/         # 導入
│
└── vol.2/             # 発展実装
    ├── cert/          # 共通証明書モジュール
    ├── HTTP2/         # HTTP/2クライアント・サーバー（ポート2000）
    └── HTTP3/         # HTTP/3クライアント・サーバー（ポート3000）
```

## セットアップ

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

### Vol.2の実行方法

詳細は`vol.2/README.md`を参照してください。

```bash
# HTTP/2サーバー
cd vol.2/HTTP2/server && go run main.go

# HTTP/3サーバー
cd vol.2/HTTP3/server && go run main.go
```

## サーバーの停止

ポート番号からプロセスを探して停止：

```bash
# プロセスIDを確認
lsof -i :2000  # HTTP/2の場合
lsof -i :3000  # HTTP/3の場合

# プロセスを停止
kill <プロセスID>
```

### ワンライナーで停止

```bash
kill $(lsof -t -i :2000)  # HTTP/2
kill $(lsof -t -i :3000)  # HTTP/3
```

## 参考資料

- [quic-goサーバーの実装例](https://qiita.com/mochi_2225/items/3a3d37b403f3b7a5c46d)