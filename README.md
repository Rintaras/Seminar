# Seminar - HTTPプロトコル実装

HTTP/1.1、HTTP/2、HTTP/3の実装例とGoプログラミングの学習プロジェクトです。

## 📥 クローン方法

```bash
# リポジトリをクローン
git clone https://github.com/Rintaras/Seminar.git
cd Seminar

# 依存関係のインストール
go mod download
```

## 🎯 推奨：Vol.2 - 性能比較研究

**HTTP/2とHTTP/3の詳細な性能比較実験**を行いたい場合は、`vol.2/`ディレクトリをご利用ください：

- 📊 5ms間隔の詳細遅延測定（0-100ms）
- 🎯 性能逆転ポイントの特定（10-15ms境界）
- 🐳 Docker環境での自動実験
- 📈 自動グラフ生成とレポート作成

詳細は **[`vol.2/README.md`](./vol.2/README.md)** をご覧ください。

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

## 🛠️ セットアップ

### 前提条件

- Go 1.24以上
- Docker & Docker Compose（vol.2の実験環境用）
- Python 3.x（分析用）

### インストール手順

```bash
# 1. リポジトリをクローン（まだの場合）
git clone https://github.com/Rintaras/Seminar.git
cd Seminar

# 2. Go モジュールの初期化（クローン後は不要）
# go mod init seminar  # ← クローンした場合は実行不要

# 3. 依存関係のダウンロード
go mod download

# 4. Python パッケージのインストール（分析用）
pip3 install matplotlib pandas seaborn
```

### Docker環境のセットアップ（vol.2用）

```bash
cd vol.2
docker-compose build
docker-compose up -d

# 動作確認
docker ps  # コンテナが起動していることを確認
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