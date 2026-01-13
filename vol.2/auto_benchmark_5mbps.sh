#!/bin/bash
# 帯域幅5Mbps制限での自動ベンチマーク＆グラフ生成スクリプト

set -e

# スクリプトのディレクトリを取得（macOS/Linux/WSL対応）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "🚀 5Mbps帯域制限ベンチマーク開始"
echo "========================================="

# Step 1: Docker環境再構築
echo ""
echo "📦 Step 1: Docker環境の準備..."
docker-compose down -v
docker-compose build
docker-compose up -d
echo "⏳ サーバー起動待機中..."
sleep 10

# 起動確認
echo ""
echo "✅ コンテナ起動状態:"
docker ps | grep -E "http|benchmark"

# Step 2: ベンチマーク実行（5条件、帯域5Mbps固定）
echo ""
echo "========================================="
echo "📊 Step 2: ベンチマーク実行（5条件、5Mbps制限）"
echo "========================================="

SESSION_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_NAME="5mbps_test"

docker exec benchmark-client bash -c "
SESSION_TIMESTAMP=$SESSION_TIMESTAMP
SESSION_NAME=$SESSION_NAME
SESSION_DIR=\"/app/results/session_\${SESSION_TIMESTAMP}_\${SESSION_NAME}\"
mkdir -p \"\$SESSION_DIR\"

cat > \"\${SESSION_DIR}/session_info.txt\" << EOF
Session Name: \${SESSION_NAME}
Start Time: \$(date '+%Y-%m-%d %H:%M:%S')
Requests per condition: 30
Total conditions: 5
Bandwidth: 5Mbps (固定)
EOF

echo \"Session directory: \$SESSION_DIR\"

conditions=(\"0 5mbit delay_0ms_bw_5mbit\" \"25 5mbit delay_25ms_bw_5mbit\" \"50 5mbit delay_50ms_bw_5mbit\" \"75 5mbit delay_75ms_bw_5mbit\" \"100 5mbit delay_100ms_bw_5mbit\")

for condition in \"\${conditions[@]}\"; do
    read -r delay bandwidth exp_name <<< \"\$condition\"
    echo \"\"
    echo \"▶ Running experiment: \$exp_name (delay=\${delay}ms, bandwidth=\${bandwidth})\"
    export PARENT_SESSION_DIR=\"\$SESSION_DIR\"
    /app/scripts/run-benchmark.sh 30 https://172.20.0.10:2000/ https://172.20.0.11:3000/ \"\$delay\" \"\$bandwidth\" \"\$exp_name\" 2>&1 | grep -E '(HTTP/[23]|TTFB|Experiment Directory)'
    sleep 2
done

cat >> \"\${SESSION_DIR}/session_info.txt\" << EOF
End Time: \$(date '+%Y-%m-%d %H:%M:%S')
Status: Completed
EOF

echo \"\"
echo \"✅ ベンチマーク完了!\"
echo \"Session: \$SESSION_DIR\"
"

echo ""
echo "========================================="
echo "✅ ベンチマーク完了"
echo "========================================="

# Step 3: グラフ生成
echo ""
echo "========================================="
echo "📈 Step 3: グラフ生成"
echo "========================================="

# プロジェクトルートに移動
cd "$SCRIPT_DIR/.."

# セッションディレクトリのパスを構築
LATEST_SESSION="vol.2/results/session_${SESSION_TIMESTAMP}_${SESSION_NAME}"

# ディレクトリが存在しない場合は最新のものを探す
if [ ! -d "$LATEST_SESSION" ]; then
    LATEST_SESSION=$(ls -td vol.2/results/session_* 2>/dev/null | head -1)
fi

if [ -n "$LATEST_SESSION" ]; then
    echo "対象セッション: $LATEST_SESSION"
    
    # Python環境の確認
    if command -v python3 &> /dev/null; then
        echo "Pythonバージョン: $(python3 --version)"
        
        # 必要なパッケージのチェック
        echo "必要なパッケージをインストール中..."
        pip3 install --quiet matplotlib pandas seaborn 2>/dev/null || true
        
        # グラフ生成
        echo "グラフを生成中..."
        if python3 vol.2/scripts/analyze_results.py "$LATEST_SESSION"; then
            # 成功した場合
            echo ""
            echo "========================================="
            echo "✅ すべて完了！"
            echo "========================================="
            echo ""
            echo "📁 結果ディレクトリ:"
            echo "   $LATEST_SESSION"
            echo ""
            
            # analysisディレクトリの確認
            if [ -d "$LATEST_SESSION/analysis" ]; then
                echo "📊 生成されたグラフ:"
                ls -lh "$LATEST_SESSION/analysis/" 2>/dev/null | tail -n +2 || echo "   （ファイルリスト取得エラー）"
                echo ""
                echo "📄 レポート:"
                echo "   $LATEST_SESSION/analysis/summary_report.txt"
                echo ""
                
                # サマリーレポートの一部を表示
                if [ -f "$LATEST_SESSION/analysis/summary_report.txt" ]; then
                    echo "📋 レポートプレビュー:"
                    echo "---"
                    head -30 "$LATEST_SESSION/analysis/summary_report.txt"
                    echo "---"
                else
                    echo "⚠️  summary_report.txt が見つかりません"
                fi
            else
                echo "⚠️  analysisディレクトリが作成されませんでした"
                echo "   パス: $LATEST_SESSION/analysis"
            fi
        else
            # エラーが発生した場合
            echo ""
            echo "❌ グラフ生成に失敗しました"
            echo ""
            echo "トラブルシューティング:"
            echo "  1. 必要なパッケージがインストールされているか確認:"
            echo "     pip3 install matplotlib pandas seaborn"
            echo ""
            echo "  2. 手動でグラフを生成:"
            echo "     python3 vol.2/scripts/analyze_results.py $LATEST_SESSION"
            echo ""
            echo "  3. Pythonのバージョンを確認:"
            echo "     python3 --version"
            echo ""
            echo "データは保存されています:"
            echo "   $LATEST_SESSION"
        fi
        
        # Finderで結果を開く
        echo ""
        echo "📂 Finderで結果を開きます..."
        open "$LATEST_SESSION/analysis/"
        
    else
        echo "⚠️  Python3が見つかりません"
        echo "Dockerで生成を試みます..."
        docker exec benchmark-client python3 /app/scripts/analyze_results.py "/app/results/session_${SESSION_TIMESTAMP}_${SESSION_NAME}" || true
    fi
else
    echo "❌ セッションディレクトリが見つかりません"
fi

echo ""
echo "========================================="
echo "🎉 処理完了！"
echo "========================================="
echo ""
echo "📊 実験条件:"
echo "  - 帯域幅: 5Mbps（固定）"
echo "  - 遅延: 0, 25, 50, 75, 100ms"
echo "  - リクエスト数: 各条件30回"
echo ""
echo "この帯域制限下でHTTP/2とHTTP/3の性能差を確認できます。"
echo ""


