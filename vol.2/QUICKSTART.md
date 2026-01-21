# クイックスタートガイド

HTTP/2 vs HTTP/3 性能比較実験を素早く始めるためのガイドです。

## 前提条件

- Docker & Docker Compose がインストールされていること
- Python 3.x（結果分析用、オプション）

## 5分で始める

### ステップ1: Docker環境の起動

```bash
cd vol.2
docker-compose up -d
```

**確認:**
```bash
docker-compose ps
# 3つのコンテナ（http2-server, http3-server, benchmark-client）が起動しているはずです
```

### ステップ2: 簡単なベンチマーク実行

```bash
# ベンチマーククライアントに接続
docker exec -it benchmark-client /bin/bash

# 理想環境でのベンチマーク（遅延0ms、損失0%、100リクエスト）
/app/scripts/run-benchmark.sh 100 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    0 \
    0
```

**実行結果例:**
```
Starting HTTP/2 benchmark...
Target: https://172.20.0.10:2000/
Requests: 100
Network Delay: 0 ms
Network Loss: 0.00%

Progress: 10/100 requests completed
Progress: 20/100 requests completed
...
Progress: 100/100 requests completed

========== Performance Summary ==========

[HTTP/2.0]
  Requests:         100
  TTFB (avg):       5.234 ms
  TTFB (min/max):   3.120 / 12.456 ms
  Total Time (avg): 6.789 ms
  ...
```

### ステップ3: 結果の確認

```bash
# Dockerコンテナから抜ける（Ctrl+D または exit）
exit

# ホスト側で結果ファイルを確認
ls -lh vol.2/results/
```

**CSVファイルの中身:**
```csv
Protocol,RequestTime,TTFB(ms),TotalTime(ms),BytesReceived,StatusCode,Error,NetworkDelay(ms),NetworkLoss(%),Throughput(KB/s)
HTTP/2.0,2026-01-13T10:15:20.123456789Z,5.234,6.789,45,200,,0,0.00,6.62
HTTP/2.0,2026-01-13T10:15:20.234567890Z,4.987,6.234,45,200,,0,0.00,7.22
...
```

## より詳細な実験

### 複数のネットワーク条件で自動実験

```bash
docker exec -it benchmark-client /bin/bash

# 11パターンのネットワーク条件で自動実験
/app/scripts/run-experiments.sh 100
```

このコマンドは以下の条件を自動的にテストします:
- 理想環境（遅延0ms、損失0%）
- 低遅延（10ms）、中遅延（50ms）、高遅延（100ms、200ms）
- 低損失（0.1%）、中損失（1%）、高損失（5%）
- 複合条件（遅延+損失の組み合わせ）

**所要時間:** 約10-15分（100リクエスト × 11条件 × 2プロトコル）

### カスタム条件でのテスト

```bash
docker exec -it benchmark-client /bin/bash

# 例: 遅延150ms、損失3%、500リクエスト
/app/scripts/run-benchmark.sh 500 \
    https://172.20.0.10:2000/ \
    https://172.20.0.11:3000/ \
    150 \
    3
```

## 結果の分析

### Pythonでグラフ生成

```bash
# ホスト側でPython環境を準備
pip install matplotlib pandas seaborn

# 分析スクリプト実行
python3 vol.2/scripts/analyze_results.py vol.2/results/
```

**生成されるファイル:**
- `vol.2/results/analysis/ttfb_comparison.png` - TTFBの比較グラフ
- `vol.2/results/analysis/throughput_comparison.png` - スループット比較
- `vol.2/results/analysis/summary_report.txt` - テキストレポート

### 手動での結果確認

```bash
# CSVファイルをExcelやGoogle Sheetsで開く
open vol.2/results/http2_delay0_loss0_*.csv
open vol.2/results/http3_delay0_loss0_*.csv
```

## よくある質問

### Q: コンテナが起動しない

```bash
# ログを確認
docker-compose logs

# コンテナを再起動
docker-compose down
docker-compose up -d
```

### Q: "tc: command not found" エラー

Dockerイメージを再ビルドしてください:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Q: 証明書エラーが出る

証明書は自動生成されますが、エラーが出る場合は再起動:
```bash
docker-compose restart http2-server http3-server
```

### Q: ベンチマーク中に接続エラー

サーバーが起動しているか確認:
```bash
docker logs http2-server
docker logs http3-server

# サーバーコンテナに接続してプロセス確認
docker exec -it http2-server ps aux | grep http
```

### Q: 結果ファイルが見つからない

volumes設定を確認:
```bash
# docker-compose.yml の benchmark-client セクションに
# volumes:
#   - ./results:/app/results
# があることを確認

# コンテナ内で確認
docker exec -it benchmark-client ls -la /app/results/
```

## クリーンアップ

### 実験結果を保持してコンテナを停止

```bash
docker-compose down
```

### 完全にクリーンアップ（結果も削除）

```bash
docker-compose down -v
rm -rf vol.2/results/*.csv
rm -rf vol.2/results/analysis/*
```

### Dockerイメージも削除

```bash
docker-compose down --rmi all -v
```

## 次のステップ

詳細な研究手法やアーキテクチャについては [`RESEARCH.md`](./RESEARCH.md) を参照してください。

- ネットワーク条件の詳細設定
- 計測メトリクスの解説
- 研究仮説と分析方法
- 論文執筆のためのデータ活用

