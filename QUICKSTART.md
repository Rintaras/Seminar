# 🚀 クイックスタートガイド

このプロジェクトを5分で始める手順です。

## 📥 ステップ1: クローン

```bash
git clone https://github.com/Rintaras/Seminar.git
cd Seminar
```

## 📦 ステップ2: 依存関係のインストール

```bash
# Go パッケージ
go mod download

# Python パッケージ（分析用）
pip3 install matplotlib pandas seaborn
```

## 🎯 ステップ3: 実行方法を選択

### オプションA: 簡易テスト（最速）

サーバーが動くか確認：

```bash
# HTTP/2テスト
go run vol.2/HTTP2/client/main.go

# HTTP/3テスト  
go run vol.2/HTTP3/client/main.go
```

### オプションB: Docker環境で性能比較実験

```bash
cd vol.2

# Docker環境を構築・起動
docker-compose up -d

# 簡易ベンチマーク（3条件、約3分）
./auto_benchmark.sh
```

実行が完了すると、`vol.2/results/session_*/analysis/`にグラフが生成されます：

```bash
# Finderで結果を開く（macOS）
open vol.2/results/session_*/analysis/
```

### オプションC: 詳細な性能比較実験（30条件）

```bash
cd vol.2

# Docker環境を起動（まだの場合）
docker-compose up -d

# 詳細ベンチマーク（30条件、約30分）
docker exec benchmark-client /app/scripts/run-experiments.sh 100 my_experiment
```

## 📊 結果の確認

実験後、以下のファイルが生成されます：

```
vol.2/results/session_YYYYMMDD_HHMMSS_実験名/
├── analysis/
│   ├── ttfb_comparison.png        # TTFBグラフ
│   ├── throughput_comparison.png  # スループットグラフ
│   └── summary_report.txt         # 詳細レポート
├── delay_0ms_bw_unlimited/        # 各実験の生データ
├── delay_5ms_bw_unlimited/
└── ...
```

## 🎯 実験結果のハイライト

プロジェクトで得られた主な発見：

- **0ms遅延**: HTTP/2が116%速い
- **5ms遅延**: HTTP/3が0.3%速い（逆転開始）
- **15ms遅延**: HTTP/3が8.2%速い（明確な逆転）
- **25ms以降**: HTTP/3が安定して優位

**逆転の境界線: 約10-15ms**

## 📚 次のステップ

詳細な情報は以下をご覧ください：

- **[vol.2/README.md](./vol.2/README.md)** - 完全なドキュメント
- **[vol.2/RESEARCH.md](./vol.2/RESEARCH.md)** - 研究手法の詳細
- **グラフを見る** - `vol.2/results/`内の最新セッション

## ⚠️ トラブルシューティング

### ポートが使用中

```bash
# ポートを使用しているプロセスを停止
docker-compose down  # Docker環境の場合
kill $(lsof -t -i :2000)  # HTTP/2
kill $(lsof -t -i :3000)  # HTTP/3
```

### Docker エラー

```bash
# コンテナを完全に削除して再構築
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Go モジュールエラー

```bash
# キャッシュをクリアして再取得
go clean -modcache
go mod download
```

## 💡 ヒント

- **短時間で試す**: `auto_benchmark.sh`（3条件、3分）
- **詳細分析**: `run-experiments.sh`（30条件、30分）
- **結果を比較**: 複数回実験して`results/`内のセッションを比較
- **カスタマイズ**: スクリプト内の条件を編集可能

## 🙋 質問・フィードバック

Issue や Pull Request を歓迎します！

- リポジトリ: https://github.com/Rintaras/Seminar



