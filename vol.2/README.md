# Vol.2 - HTTP/2 & HTTP/3実装

HTTP/2とHTTP/3のシンプルなクライアント・サーバー実装と、性能比較研究用のベンチマーク環境です。

## 🚀 クイックスタート

**性能比較実験をすぐに始めたい方は [`QUICKSTART.md`](./QUICKSTART.md) をご覧ください。**

**詳細な研究手法については [`RESEARCH.md`](./RESEARCH.md) をご覧ください。**

## プロジェクト構成

```
vol.2/
├── cert/                    # 共通証明書モジュール
│   ├── cert.go             # 証明書生成・管理
│   ├── cert.crt            # 自動生成される証明書（gitignore）
│   └── cert.key            # 自動生成される秘密鍵（gitignore）
├── benchmark/              # ベンチマーク用共通モジュール
│   └── metrics.go          # 性能計測・記録機能
├── HTTP2/                  # HTTP/2実装
│   ├── server/             # HTTP/2サーバー（ポート2000）
│   ├── client/             # HTTP/2クライアント（検証用）
│   └── benchmark-client/   # HTTP/2ベンチマーククライアント
├── HTTP3/                  # HTTP/3実装
│   ├── server/             # HTTP/3サーバー（ポート3000）
│   ├── client/             # HTTP/3クライアント（検証用）
│   └── benchmark-client/   # HTTP/3ベンチマーククライアント
├── scripts/                # 実験用スクリプト
│   ├── set-network-conditions.sh    # ネットワーク条件設定
│   ├── reset-network-conditions.sh  # ネットワーク条件リセット
│   ├── run-benchmark.sh             # ベンチマーク実行
│   ├── run-experiments.sh           # 複数条件自動実験
│   └── analyze_results.py           # 結果分析スクリプト
├── results/                # 実験結果（gitignore）
├── Dockerfile              # Dockerイメージ定義
├── docker-compose.yml      # Docker環境定義
├── QUICKSTART.md           # クイックスタートガイド
└── RESEARCH.md             # 研究詳細ドキュメント
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

## 性能比較ベンチマーク

### Docker環境での実行

```bash
# Docker環境の起動
docker-compose up -d

# ベンチマーク実行（遅延50ms、損失1%、100リクエスト）
docker exec -it benchmark-client /app/scripts/run-benchmark.sh 100 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    50 \
    1

# 複数条件での自動実験
docker exec -it benchmark-client /app/scripts/run-experiments.sh 100
```

### ローカル環境での実行

```bash
# HTTP/2サーバー起動
go run vol.2/HTTP2/server/main.go &

# HTTP/3サーバー起動
go run vol.2/HTTP3/server/main.go &

# HTTP/2ベンチマーク
go run vol.2/HTTP2/benchmark-client/main.go \
    -url https://localhost:2000/ \
    -n 100 \
    -o results/http2_test.csv

# HTTP/3ベンチマーク
go run vol.2/HTTP3/benchmark-client/main.go \
    -url https://localhost:3000/ \
    -n 100 \
    -o results/http3_test.csv
```

### 計測メトリクス

- **TTFB (Time To First Byte)**: リクエスト送信から最初のバイトを受信するまでの時間
- **Total Time**: リクエスト送信から全データ受信完了までの時間
- **Throughput**: 単位時間あたりのデータ転送量 (KB/s)

### 結果分析

```bash
# Pythonでグラフ生成
pip install matplotlib pandas seaborn
python3 vol.2/scripts/analyze_results.py vol.2/results/

# 生成される分析結果:
# - results/analysis/ttfb_comparison.png      # TTFBの比較グラフ
# - results/analysis/throughput_comparison.png # スループット比較
# - results/analysis/ttfb_heatmap.png         # 条件別ヒートマップ
# - results/analysis/summary_report.txt       # テキストレポート
```

## 注意事項

- HTTP/2: TCP上で動作、HTTP/1.1フォールバックあり
- HTTP/3: QUIC（UDP）上で動作、TLS 1.3必須
- 両方のサーバーは同時起動可能（異なるポート）
- 証明書は両サーバーで共有
- `go run`を推奨（`go build`するとバイナリが生成される）

## 参考資料

- [`QUICKSTART.md`](./QUICKSTART.md) - 5分で始めるクイックスタートガイド
- [`RESEARCH.md`](./RESEARCH.md) - 詳細な研究手法とアーキテクチャ