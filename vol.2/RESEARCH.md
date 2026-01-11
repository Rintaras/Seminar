# HTTP/2 vs HTTP/3 性能比較研究

## 研究目的

1. **ネットワーク特性による性能変化の調査**
   - 遅延（Latency）やパケット損失率（Loss）が、HTTP/2とHTTP/3の応答速度やスループットにどう影響するかを明らかにする

2. **「HTTP/2優位説」の検証**
   - 高速・安定したインターネット環境において、HTTP/2の方がHTTP/3よりも効率が良いとされる先行研究に基づき、その「逆転の境界線」がどこにあるのかをGoの実装で確かめる

## アーキテクチャ

### コンポーネント構成

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Network                         │
│                  (172.20.0.0/16)                       │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ HTTP/2 Server│  │ HTTP/3 Server│  │ Benchmark   │ │
│  │ :2000 (TCP) │  │ :3000 (UDP)  │  │ Client      │ │
│  │ 172.20.0.10  │  │ 172.20.0.11  │  │ 172.20.0.20 │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│         ▲                ▲                   │         │
│         │                │                   │         │
│         └────────────────┴───────────────────┘         │
│              tc (Traffic Control)                      │
│          - 遅延制御 (delay)                            │
│          - パケット損失 (loss)                         │
│          - 帯域幅制限 (bandwidth)                      │
└─────────────────────────────────────────────────────────┘
```

### ディレクトリ構成

```
vol.2/
├── HTTP2/
│   ├── server/                    # HTTP/2サーバー
│   ├── client/                    # HTTP/2クライアント（検証用）
│   └── benchmark-client/          # HTTP/2ベンチマーククライアント
├── HTTP3/
│   ├── server/                    # HTTP/3サーバー
│   ├── client/                    # HTTP/3クライアント（検証用）
│   └── benchmark-client/          # HTTP/3ベンチマーククライアント
├── benchmark/
│   └── metrics.go                 # 計測・記録モジュール
├── cert/
│   └── cert.go                    # 証明書管理
├── scripts/
│   ├── set-network-conditions.sh  # ネットワーク条件設定
│   ├── reset-network-conditions.sh # ネットワーク条件リセット
│   ├── run-benchmark.sh           # 単一条件ベンチマーク
│   ├── run-experiments.sh         # 複数条件自動実験
│   └── analyze_results.py         # 結果分析スクリプト
├── results/                       # 実験結果出力先
├── Dockerfile                     # Dockerイメージ定義
└── docker-compose.yml             # Docker環境定義
```

## セットアップ

### 1. Docker環境の構築

```bash
cd vol.2

# Dockerイメージのビルド
docker-compose build

# コンテナの起動
docker-compose up -d

# コンテナの状態確認
docker-compose ps
```

### 2. 動作確認

```bash
# HTTP/2サーバーのログ確認
docker logs http2-server

# HTTP/3サーバーのログ確認
docker logs http3-server

# ベンチマーククライアントに接続
docker exec -it benchmark-client /bin/bash
```

## 実験の実行

### パターン1: 単一条件でのベンチマーク

```bash
# ベンチマーククライアントコンテナに接続
docker exec -it benchmark-client /bin/bash

# 例: 遅延50ms、パケット損失1%、リクエスト数100回
/app/scripts/run-benchmark.sh 100 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    50 \
    1
```

**パラメータ:**
- 第1引数: リクエスト数
- 第2引数: HTTP/2サーバーURL
- 第3引数: HTTP/3サーバーURL
- 第4引数: 遅延 (ms)
- 第5引数: パケット損失率 (%)

### パターン2: 複数条件での自動実験

```bash
# ベンチマーククライアントコンテナに接続
docker exec -it benchmark-client /bin/bash

# 自動実験スクリプトの実行（各条件100リクエスト）
/app/scripts/run-experiments.sh 100
```

**実験条件（デフォルト）:**
- ベースライン: 遅延0ms、損失0%
- 低遅延: 遅延10ms、損失0%
- 中遅延: 遅延50ms、損失0%
- 高遅延: 遅延100ms、損失0%
- 非常に高い遅延: 遅延200ms、損失0%
- 低損失: 遅延0ms、損失0.1%
- 中損失: 遅延0ms、損失1%
- 高損失: 遅延0ms、損失5%
- 複合1: 遅延50ms、損失1%
- 複合2: 遅延100ms、損失1%
- 複合3: 遅延100ms、損失5%

### パターン3: 手動でのネットワーク条件設定

```bash
docker exec -it benchmark-client /bin/bash

# ネットワーク条件を設定（遅延100ms、損失2%）
/app/scripts/set-network-conditions.sh eth0 100 2

# HTTP/2ベンチマーク
/app/http2-benchmark -url https://172.20.0.10:2000/ -n 100 -o /app/results/http2_custom.csv -delay 100 -loss 2

# HTTP/3ベンチマーク
/app/http3-benchmark -url https://172.20.0.11:3000/ -n 100 -o /app/results/http3_custom.csv -delay 100 -loss 2

# ネットワーク条件をリセット
/app/scripts/reset-network-conditions.sh eth0
```

## 結果の分析

### 1. 結果ファイルの取得

実験結果はホストの `vol.2/results/` ディレクトリに自動保存されます。

```bash
# 結果ファイルの確認
ls -lh vol.2/results/

# 例:
# http2_delay0_loss0_20260113_101520.csv
# http3_delay0_loss0_20260113_101520.csv
# http2_delay50_loss1_20260113_101545.csv
# http3_delay50_loss1_20260113_101545.csv
```

### 2. CSV形式のデータ構造

各CSVファイルには以下のカラムが含まれます：

| カラム名 | 説明 |
|---------|------|
| Protocol | プロトコル (HTTP/2.0 or HTTP/3.0) |
| RequestTime | リクエスト開始時刻 |
| TTFB(ms) | Time To First Byte (ミリ秒) |
| TotalTime(ms) | 全体の転送時間 (ミリ秒) |
| BytesReceived | 受信バイト数 |
| StatusCode | HTTPステータスコード |
| Error | エラー内容（あれば） |
| NetworkDelay(ms) | 設定された遅延 |
| NetworkLoss(%) | 設定されたパケット損失率 |
| Throughput(KB/s) | スループット (KB/秒) |

### 3. グラフ生成と分析

```bash
# Python環境が必要（matplotlib, pandas, seaborn）
pip install matplotlib pandas seaborn

# 分析スクリプトの実行
python3 vol.2/scripts/analyze_results.py vol.2/results/

# 以下のファイルが results/analysis/ に生成されます:
# - ttfb_comparison.png      : TTFBの比較グラフ
# - throughput_comparison.png: スループットの比較グラフ
# - ttfb_heatmap.png         : TTFBヒートマップ
# - summary_report.txt       : サマリーレポート
```

## 計測メトリクス詳細

### TTFB (Time To First Byte)
- **定義**: リクエスト送信から最初のバイトを受信するまでの時間
- **重要性**: サーバー処理速度とネットワーク遅延の指標
- **HTTP/2**: `httptrace.ClientTrace.GotFirstResponseByte` で計測
- **HTTP/3**: 最初の1バイトを読み取るまでの時間で計測

### Total Time
- **定義**: リクエスト送信から全データ受信完了までの時間
- **重要性**: エンドユーザー体感速度の指標
- **計測**: `time.Since(startTime)` で全体時間を記録

### Throughput
- **定義**: 単位時間あたりのデータ転送量 (KB/s)
- **計算式**: `BytesReceived / TotalTime.Seconds() / 1024`
- **重要性**: 帯域幅利用効率の指標

## 期待される研究成果

### 仮説1: 理想環境ではHTTP/2が優位
- **予想**: 遅延0ms、損失0%の環境でHTTP/2のTTFBが短い
- **理由**: TCP接続の確立コストがQUICより低い

### 仮説2: 高遅延環境ではHTTP/3が優位
- **予想**: 遅延100ms以上でHTTP/3のTTFBが短い
- **理由**: QUICの0-RTT接続再開機能

### 仮説3: パケット損失環境ではHTTP/3が優位
- **予想**: 損失1%以上でHTTP/3のスループットが高い
- **理由**: HTTP/3のストリーム独立性（HOL Blocking解消）

### 逆転境界線の発見
- **目標**: どの条件でHTTP/2とHTTP/3の性能が逆転するかを特定
- **アプローチ**: 遅延とパケット損失の組み合わせで境界を可視化

## トラブルシューティング

### コンテナが起動しない

```bash
# ログ確認
docker-compose logs

# コンテナ再起動
docker-compose down
docker-compose up -d
```

### ネットワーク条件が適用されない

```bash
# クライアントコンテナに接続
docker exec -it benchmark-client /bin/bash

# 現在の tc 設定を確認
tc qdisc show dev eth0

# 設定をリセット
/app/scripts/reset-network-conditions.sh eth0
```

### 証明書エラー

```bash
# 証明書の再生成
docker exec -it http2-server /bin/bash
rm -f /app/cert/*.crt /app/cert/*.key
# サーバー再起動で自動生成

docker-compose restart http2-server http3-server
```

## 参考文献

- RFC 9114: HTTP/3
- RFC 9000: QUIC: A UDP-Based Multiplexed and Secure Transport
- RFC 7540: Hypertext Transfer Protocol Version 2 (HTTP/2)

## ライセンス

This research project is for educational purposes.

