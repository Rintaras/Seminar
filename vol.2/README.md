# Vol.2 - HTTP/2 & HTTP/3実装

HTTP/2とHTTP/3のシンプルなクライアント・サーバー実装と、性能比較研究用のベンチマーク環境です。

## 🎯 主な特徴

- **詳細な性能測定**: 5ms間隔の細かい遅延測定（0-100ms、全30条件）
- **性能逆転ポイントの特定**: HTTP/2とHTTP/3の優位性が切り替わる境界線を解析
- **自動化された実験環境**: Docker + tc コマンドによる再現可能なネットワーク条件設定
- **包括的な分析**: Python（matplotlib）による自動グラフ生成とレポート作成

## 📥 リポジトリのクローン

### 1. リポジトリをクローン

```bash
git clone https://github.com/Rintaras/Seminar.git
cd Seminar
```

### 2. 必要な依存関係のインストール

```bash
# Go モジュールのダウンロード
go mod download

# Python パッケージのインストール（分析用）
pip3 install matplotlib pandas seaborn
```

### 3. Docker環境のセットアップ（推奨）

```bash
cd vol.2
docker-compose build
docker-compose up -d
```

### 4. 動作確認

```bash
# オプションA: 簡易テスト（3条件、帯域無制限）
./vol.2/auto_benchmark.sh

# オプションB: 5Mbps帯域制限ベンチマーク（5条件）
./vol.2/auto_benchmark_5mbps.sh

# オプションC: 手動テスト
go run vol.2/HTTP2/client/main.go
go run vol.2/HTTP3/client/main.go
```

#### 📊 各ベンチマークの比較

| スクリプト | 条件数 | 帯域制限 | 遅延範囲 | 実行時間 | 用途 |
|-----------|--------|----------|----------|----------|------|
| `auto_benchmark.sh` | 3 | 無制限/1Mbps | 0, 50, 100ms | 約3分 | 基本的な性能比較 |
| `auto_benchmark_5mbps.sh` | 5 | **5Mbps固定** | 0, 25, 50, 75, 100ms | 約5分 | 中速回線での詳細比較 |
| `run-experiments.sh` | 30 | 多様 | 0-100ms (5ms刻み) | 約30分 | 包括的な研究 |

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

### 💻 プラットフォーム別の実行方法

#### macOS / Linux
シェルスクリプト（`.sh`）をそのまま実行できます：
```bash
cd vol.2
./auto_benchmark.sh
```

#### Windows
以下のいずれかの方法で実行してください：

**方法1: WSL (Windows Subsystem for Linux) を使用 - 推奨**
```bash
# WSLを開いて実行
cd vol.2
bash auto_benchmark.sh
```

**方法2: Git Bash を使用**
```bash
# Git Bashを開いて実行
cd vol.2
bash auto_benchmark.sh
```

**方法3: Windowsバッチファイル（WSL必須）**
```cmd
cd vol.2
auto_benchmark.bat
```

**注意**: Windowsでは`.sh`ファイルをダブルクリックしても正しく実行されません。必ず上記の方法で実行してください。

#### Windows: 結果の確認方法
ベンチマーク実行後、結果を確認するには：

**方法1: PowerShell スクリプト（推奨）**
```powershell
# PowerShellで実行（最も高機能）
cd vol.2
powershell -ExecutionPolicy Bypass -File view_results.ps1
```

**方法2: バッチファイル**
```cmd
cd vol.2
view_results.bat
```

**方法3: エクスプローラーで直接開く**
```
vol.2\results\session_YYYYMMDD_HHMMSS_*\
```

### 🧪 動作確認テスト（推奨・最初に実行）

ベンチマーク環境が正しくセットアップされているか確認：

```bash
cd vol.2

# 環境チェック（Windows）
check_setup.bat

# または環境チェック（macOS/Linux/WSL）
bash test_benchmark.sh
```

このテストスクリプトは：
- ✅ Docker環境を確認
- ✅ コンテナの起動状態を確認
- ✅ 簡易ベンチマーク（5リクエスト）を実行
- ✅ 結果ファイルが正しく保存されるか確認
- ✅ 問題があれば診断とトラブルシューティングを提示

**問題が見つかった場合は、まずこれを実行してください！**

### 🚀 クイックテスト（サーバー接続確認）

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

**複数実験セッション（30条件自動実行）**

```bash
# セッション名を指定して複数条件を自動実行
docker exec benchmark-client /app/scripts/run-experiments.sh [リクエスト数] [セッション名]

# 例: 包括的な性能評価（0-100ms を5ms間隔で詳細測定）
docker exec benchmark-client /app/scripts/run-experiments.sh 100 comprehensive_test

# セッション結果は以下のように整理されます:
# results/session_20260113_080000_comprehensive_test/
#   ├── session_info.txt                # セッション情報
#   ├── delay_0ms_bw_unlimited/         # 遅延0ms（帯域無制限）
#   ├── delay_5ms_bw_unlimited/         # 遅延5ms
#   ├── delay_10ms_bw_unlimited/        # 遅延10ms
#   ├── delay_15ms_bw_unlimited/        # 遅延15ms
#   ├── ...                             # 5ms刻みで継続
#   ├── delay_95ms_bw_unlimited/        # 遅延95ms
#   ├── delay_100ms_bw_unlimited/       # 遅延100ms
#   ├── delay_0ms_bw_100mbit/           # 高速帯域（100Mbps）
#   ├── delay_0ms_bw_10mbit/            # 中速帯域（10Mbps）
#   ├── delay_0ms_bw_1mbit/             # 低速帯域（1Mbps）
#   ├── delay_25ms_bw_10mbit/           # 複合条件（25ms, 10Mbps）
#   ├── delay_50ms_bw_10mbit/           # 複合条件（50ms, 10Mbps）
#   ├── delay_75ms_bw_10mbit/           # 複合条件（75ms, 10Mbps）
#   ├── delay_100ms_bw_10mbit/          # 複合条件（100ms, 10Mbps）
#   ├── delay_50ms_bw_1mbit/            # 複合条件（50ms, 1Mbps）
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

## 📊 実験結果サマリー

### 主要な発見

**30条件・900リクエストの詳細測定**により、HTTP/2とHTTP/3の性能逆転ポイントを特定しました。

#### 🏆 性能逆転の詳細（遅延による影響）

| 遅延条件 | 勝者 | HTTP/2 TTFB | HTTP/3 TTFB | 性能差 | 備考 |
|---------|------|-------------|-------------|--------|------|
| **0ms** | HTTP/2 | 0.712ms | 1.542ms | **+116%** | 理想環境でHTTP/2が圧倒的優位 |
| **5ms** | HTTP/3 | 8.228ms | 8.205ms | **+0.3%** | 逆転開始（ほぼ同等） |
| **10ms** | HTTP/2 | 14.082ms | 14.665ms | +4.1% | 拮抗ゾーン |
| **15ms** | HTTP/3 | 20.675ms | 19.114ms | **+8.2%** | 明確な逆転 |
| **20ms** | HTTP/3 | 27.951ms | 24.178ms | **+15.6%** | HTTP/3が有利 |
| **25ms+** | HTTP/3 | - | - | **安定優位** | 以降HTTP/3が一貫して優位 |

#### 📈 重要な境界線

```
低遅延（0-10ms）     → HTTP/2が優位
拮抗ゾーン（10-15ms） → 性能が逆転する遷移領域
中～高遅延（15ms+）   → HTTP/3が明確に優位
```

#### 🔍 技術的考察

1. **HTTP/2の優位性（低遅延環境）**
   - TCP接続の再利用が効率的
   - ヘッドオブラインブロッキングの影響が小さい
   - プロトコルオーバーヘッドが少ない

2. **HTTP/3の優位性（中～高遅延環境）**
   - QUICの接続確立が高速（0-RTT）
   - パケットロス時の復旧が迅速
   - ストリーム独立性による影響分離

3. **逆転ポイント（10-15ms）**
   - TCP vs QUICの特性が拮抗
   - ネットワーク条件に敏感
   - 実装の最適化で変動する可能性あり

### 帯域幅による影響

| 帯域制限 | HTTP/2 | HTTP/3 | 勝者 |
|---------|--------|--------|------|
| **無制限** | 0.712ms | 1.542ms | HTTP/2 (+116%) |
| **100Mbps** | 1.206ms | 1.715ms | HTTP/2 (+42%) |
| **10Mbps** | 0.892ms | 1.430ms | HTTP/2 (+60%) |
| **1Mbps** | 0.945ms | 1.305ms | HTTP/2 (+38%) |

**結論**: 帯域制限のみの場合、低遅延環境と同様にHTTP/2が優位

### 実用的な推奨事項

#### HTTP/2を選択すべき場合
- ✅ 低遅延ネットワーク（<10ms）
- ✅ 社内LAN・データセンター間通信
- ✅ CDN配信（エッジが近い場合）

#### HTTP/3を選択すべき場合
- ✅ 中～高遅延ネットワーク（>15ms）
- ✅ モバイルネットワーク
- ✅ パケット損失が多い環境
- ✅ 頻繁な接続確立が必要な場合

## 🛠️ 技術スタック

### プロトコル実装
- **HTTP/2**: Go標準ライブラリ（`net/http` + `golang.org/x/net/http2`）
- **HTTP/3**: `github.com/quic-go/quic-go/http3`（QUIC実装）
- **TLS**: 自己署名証明書（RSA 2048bit）

### ベンチマーク・分析
- **性能計測**: Go（カスタム実装）
  - TTFB（Time To First Byte）
  - Total Time
  - Throughput
- **ネットワーク制御**: Linux `tc`（traffic control）コマンド
  - 遅延（netem qdisc）
  - 帯域制限（tbf qdisc）
- **データ分析**: Python
  - pandas（データ処理）
  - matplotlib + seaborn（グラフ生成）

### インフラ
- **コンテナ**: Docker + Docker Compose
- **ネットワーク**: カスタムブリッジネットワーク（172.20.0.0/16）
- **OS**: Alpine Linux（Docker内）

### 実験設計
- **測定間隔**: 5ms（0-100ms）
- **条件数**: 30パターン
- **リクエスト数**: 30-100/条件（カスタマイズ可能）
- **実験時間**: 約25-30分（30条件×30リクエスト）

## 注意事項

- HTTP/2: TCP上で動作、HTTP/1.1フォールバックあり
- HTTP/3: QUIC（UDP）上で動作、TLS 1.3必須
- 両方のサーバーは同時起動可能（異なるポート）
- 証明書は両サーバーで共有
- `go run`を推奨（`go build`するとバイナリが生成される）
- Docker環境では`tc`コマンドで正確なネットワーク制御が可能

## 🐛 トラブルシューティング

### ベンチマーク実行後にファイルが保存されない

**問題**: ベンチマークを実行したが、`results`ディレクトリにファイルが作成されない

**診断方法**:

1. **環境診断スクリプトを実行**（最優先）
   ```bash
   # Windows
   cd vol.2
   debug_docker.bat
   
   # macOS/Linux/WSL
   cd vol.2
   bash test_benchmark.sh
   ```

2. **Docker コンテナの状態を確認**
   ```bash
   docker ps
   # http2-server, http3-server, benchmark-client が起動しているか確認
   ```

3. **ボリュームマウントを確認**
   ```bash
   docker inspect benchmark-client | grep -A5 Mounts
   # vol.2/results が /app/results にマウントされているか確認
   ```

4. **Docker内でファイルが作成されているか確認**
   ```bash
   docker exec benchmark-client ls -la /app/results/
   ```

**よくある原因と解決方法**:

| 原因 | 解決方法 |
|------|---------|
| Docker Desktop が起動していない | Docker Desktop を起動して数分待つ |
| コンテナが起動していない | `docker-compose up -d` を実行 |
| ボリュームマウントが設定されていない | `docker-compose down -v && docker-compose up -d` |
| 権限の問題（Linux/WSL） | `sudo chmod 777 results/` |
| Windowsのパス問題 | WSLまたはGit Bashから実行 |
| resultsディレクトリがない | `mkdir results` を実行 |

**完全リセット** （最終手段）:
```bash
cd vol.2
docker-compose down -v
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
bash test_benchmark.sh
```

### Windows: バッチファイル（.bat）をダブルクリックしてもすぐ閉じる

**問題**: `.bat`ファイルをダブルクリックすると、ウィンドウが開いてすぐ閉じる

**原因**: エラーが発生しているが、メッセージが表示される前にウィンドウが閉じる

**解決方法（推奨順）**:

1. **コマンドプロンプトから実行** - 最も確実
   ```cmd
   # Win+R を押して「cmd」と入力
   cd /d "C:\Users\[ユーザー名]\Documents\Research\Seminar\vol.2"
   
   # 環境チェック（推奨）
   check_setup.bat
   
   # ベンチマーク実行
   bash auto_benchmark.sh
   
   # 結果確認
   view_results.bat
   ```

2. **PowerShellから実行**
   ```powershell
   cd "C:\Users\[ユーザー名]\Documents\Research\Seminar\vol.2"
   bash auto_benchmark.sh
   powershell -ExecutionPolicy Bypass -File view_results.ps1
   ```

3. **環境チェックスクリプトを実行**
   ```cmd
   # vol.2ディレクトリで右クリック → ターミナルで開く
   check_setup.bat
   ```
   このスクリプトが、Docker、WSL、ディレクトリ構造などをチェックして問題を診断します。

📄 **詳細は `WINDOWS_README.txt` を参照してください**

### Windows: スクリプトをダブルクリックしてもすぐ終了する（.sh）

**問題**: `.sh`ファイルをWindowsでダブルクリックすると、ウィンドウが開いてすぐ閉じる

**原因**: シェルスクリプト（`.sh`）はWindowsでは直接実行できません

**解決方法**:
1. **WSL (Windows Subsystem for Linux) を使用** - 推奨
   ```bash
   # PowerShellまたはコマンドプロンプトで
   wsl
   cd /mnt/c/Users/[あなたのユーザー名]/Documents/Research/Seminar/vol.2
   bash auto_benchmark.sh
   ```

2. **Git Bash を使用**
   ```bash
   # Git Bashを開いて
   cd vol.2
   bash auto_benchmark.sh
   ```

3. **Windowsバッチファイルを使用**（WSL必須）
   ```cmd
   cd vol.2
   auto_benchmark.bat
   ```

### Docker: ポートが既に使用されている

**問題**: `bind: address already in use`エラー

**解決方法**:
```bash
# 既存のコンテナを停止
docker-compose down -v

# プロセスを確認して停止
# macOS/Linux:
lsof -ti:2000,3000 | xargs kill -9

# Windows (PowerShell):
Get-NetTCPConnection -LocalPort 2000,3000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object {Stop-Process -Id $_ -Force}
```

### Python: グラフが生成されない

**問題**: `python3: command not found`または`ModuleNotFoundError`

**解決方法**:
```bash
# Python3をインストール
# macOS:
brew install python3

# Ubuntu/WSL:
sudo apt update && sudo apt install python3 python3-pip

# パッケージをインストール
pip3 install matplotlib pandas seaborn
```

### Docker: イメージのビルドに失敗する

**問題**: Goバージョンエラーや依存関係エラー

**解決方法**:
```bash
# クリーンビルド
docker-compose down -v
docker system prune -a  # 注意: 全てのDockerイメージを削除
docker-compose build --no-cache
docker-compose up -d
```

## 参考資料

- [`QUICKSTART.md`](./QUICKSTART.md) - 5分で始めるクイックスタートガイド
- [`RESEARCH.md`](./RESEARCH.md) - 詳細な研究手法とアーキテクチャ