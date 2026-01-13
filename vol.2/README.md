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

### 🚀 クイックテスト（最も簡単）

サーバーが動いているか素早く確認：

```bash
# HTTP/2のテスト
go run vol.2/HTTP2/client/main.go

# HTTP/3のテスト
go run vol.2/HTTP3/client/main.go
```

**期待される出力:**
```
Status: 200 OK
Protocol: HTTP/2.0
Response:
Hello HTTP/2!
Protocol: HTTP/2.0
```

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

#### 簡易テスト（レスポンス確認）

```bash
# Docker環境の起動
docker-compose up -d

# シンプルなテスト
docker exec benchmark-client /app/http2-benchmark -url https://172.20.0.10:2000/ -n 1
docker exec benchmark-client /app/http3-benchmark -url https://172.20.0.11:3000/ -n 1
```

#### ベンチマーク実行

**単一実験（実験名指定可能）**

```bash
# 基本形式
docker exec benchmark-client /app/scripts/run-benchmark.sh \
    [リクエスト数] \
    [HTTP/2 URL] \
    [HTTP/3 URL] \
    [遅延ms] \
    [損失率%] \
    [実験名(オプション)]

# 例1: 理想環境でのテスト（帯域無制限）
docker exec benchmark-client /app/scripts/run-benchmark.sh \
    100 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    0 \
    0 \
    delay_0ms_bw_unlimited

# 例2: 高遅延環境（帯域無制限）
docker exec benchmark-client /app/scripts/run-benchmark.sh \
    100 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    100 \
    0 \
    delay_100ms_bw_unlimited

# 例3: 帯域制限環境（1Mbps）
docker exec benchmark-client /app/scripts/run-benchmark.sh \
    100 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    0 \
    1mbit \
    delay_0ms_bw_1mbit

# 実験結果は以下のように整理されます:
# results/20260113_080000_delay_0ms_bw_unlimited/
#   ├── experiment_info.txt
#   ├── http2_results.csv
#   └── http3_results.csv
```

**複数実験セッション（11条件自動実行）**

```bash
# セッション名を指定して複数条件を自動実行
docker exec benchmark-client /app/scripts/run-experiments.sh [リクエスト数] [セッション名]

# 例: 包括的な性能評価
docker exec benchmark-client /app/scripts/run-experiments.sh 100 comprehensive_test

# セッション結果は以下のように整理されます:
# results/session_20260113_080000_comprehensive_test/
#   ├── session_info.txt                # セッション情報
#   ├── delay_0ms_bw_unlimited/         # 理想環境（遅延0ms, 帯域無制限）
#   │   ├── experiment_info.txt
#   │   ├── http2_results.csv
#   │   └── http3_results.csv
#   ├── delay_10ms_bw_unlimited/        # 低遅延（10ms, 帯域無制限）
#   ├── delay_50ms_bw_unlimited/        # 中遅延（50ms, 帯域無制限）
#   ├── delay_100ms_bw_unlimited/       # 高遅延（100ms, 帯域無制限）
#   ├── delay_200ms_bw_unlimited/       # 非常に高い遅延（200ms, 帯域無制限）
#   ├── delay_0ms_bw_100mbit/           # 高速帯域（100Mbps）
#   ├── delay_0ms_bw_10mbit/            # 中速帯域（10Mbps）
#   ├── delay_0ms_bw_1mbit/             # 低速帯域（1Mbps）
#   ├── delay_50ms_bw_10mbit/           # 複合条件（50ms, 10Mbps）
#   ├── delay_100ms_bw_10mbit/          # 複合条件（100ms, 10Mbps）
#   └── delay_100ms_bw_1mbit/           # 過酷な条件（100ms, 1Mbps）
```

### ローカル環境での実行

#### 簡易テスト（レスポンス確認）

```bash
# サーバー起動
go run vol.2/HTTP2/server/main.go &
go run vol.2/HTTP3/server/main.go &

# シンプルなテスト
go run vol.2/HTTP2/client/main.go
go run vol.2/HTTP3/client/main.go
```

#### ベンチマーク実行

```bash
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

### 結果管理

**ディレクトリ構造**

```
vol.2/results/
├── session_20260113_080000_comprehensive/  # セッション単位
│   ├── session_info.txt                    # セッション情報
│   ├── delay_0ms_bw_unlimited/             # 各実験（ネットワーク条件で命名）
│   │   ├── experiment_info.txt             # 実験パラメータ
│   │   ├── http2_results.csv               # HTTP/2結果
│   │   └── http3_results.csv               # HTTP/3結果
│   ├── delay_50ms_bw_unlimited/
│   ├── delay_100ms_bw_1mbit/
│   └── ...
│   └── analysis/                           # 分析結果
│       ├── ttfb_comparison.png             # TTFBグラフ
│       ├── throughput_comparison.png       # スループットグラフ
│       ├── ttfb_heatmap.png                # ヒートマップ
│       └── summary_report.txt              # サマリーレポート
├── 20260113_090000_quick_test_delay0ms_bw_unlimited/  # 単一実験
│   ├── experiment_info.txt
│   ├── http2_results.csv
│   └── http3_results.csv
└── old_results/                            # 古い結果（任意）
```

**利点**
- ✅ 実験ごとにディレクトリが分かれて整理しやすい
- ✅ `experiment_info.txt`で実験条件を記録
- ✅ セッション単位で複数実験をまとめて管理
- ✅ タイムスタンプで実験の時系列を追跡可能

### 結果分析

```bash
# Pythonでグラフ生成（セッション全体を分析）
pip install matplotlib pandas seaborn
python3 vol.2/scripts/analyze_results.py vol.2/results/session_20260113_080000_comprehensive/

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