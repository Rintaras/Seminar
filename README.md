# Seminar - HTTPプロトコル実装

HTTP/1.1、HTTP/2、HTTP/3の実装例とゼミ生のプロトコル学習プロジェクトです。

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

- 📊 詳細な性能測定（0-100ms、5ms間隔または1ms間隔）
- 🎯 性能逆転ポイントの特定（10-15ms境界）
- 🐳 Docker環境での自動実験（完全OS非依存）
- 📈 高品質なスムージンググラフ自動生成（Savitzky-Golay + スプライン補間）
- 🎨 標準偏差の可視化と詳細なレポート作成

**詳細は [`vol.2/README.md`](./vol.2/README.md) と [`vol.2/ARCHITECTURE.md`](./vol.2/ARCHITECTURE.md) をご覧ください。**

## プロジェクト構成

```
Seminar/
├── Vol.1/              # 基礎実装
│   ├── HTTP1.1/       # HTTP/1.1サーバー
│   ├── HTTP2/         # HTTP/2サーバー（単一ファイル）
│   ├── Sum/           # 基本的なGoプログラム
│   └── intro/         # 導入
│
└── vol.2/             # 発展実装・性能比較研究
    ├── cert/          # 共通証明書モジュール
    ├── HTTP2/         # HTTP/2クライアント・サーバー（ポート2000）
    ├── HTTP3/         # HTTP/3クライアント・サーバー（ポート3000）
    ├── scripts/       # ベンチマーク・分析スクリプト
    ├── auto_benchmark.sh      # 自動ベンチマーク（3条件）
    ├── auto_benchmark_5mbps.sh # 自動ベンチマーク（5Mbps版）
    ├── ARCHITECTURE.md         # 実行環境の詳細図解
    └── README.md               # 詳細ドキュメント
```

## 🛠️ セットアップ

### 前提条件

- Go 1.24以上
- Docker & Docker Compose（vol.2の実験環境用）
- **注意**: Pythonのインストールは不要です（グラフ生成はDocker内で自動実行）

### インストール手順

```bash
# 1. リポジトリをクローン（まだの場合）
git clone https://github.com/Rintaras/Seminar.git
cd Seminar

# 2. Go モジュールの初期化（クローン後は不要）
# go mod init seminar  # ← クローンした場合は実行不要

# 3. 依存関係のダウンロード
go mod download

# 注意: Pythonのインストールは不要です
# グラフ生成はDocker内で自動的に実行されます（OS非依存）
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

#### 自動ベンチマーク（推奨）

```bash
cd vol.2

# オプションA: 簡易テスト（3条件、帯域無制限）
./auto_benchmark.sh          # macOS/Linux
auto_benchmark.bat           # Windows

# オプションB: 5Mbps帯域制限ベンチマーク（5条件）
./auto_benchmark_5mbps.sh    # macOS/Linux
auto_benchmark_5mbps.bat     # Windows
```

#### 手動実行（開発・検証用）

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