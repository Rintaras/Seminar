#!/bin/bash
# 完全自動ベンチマーク＆グラフ生成スクリプト

set -e

# スクリプトのディレクトリを取得（macOS/Linux/WSL対応）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "🚀 完全自動テスト開始"
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

# Step 2: ベンチマーク実行（24条件: 6遅延 × 4帯域幅）
echo ""
echo "========================================="
echo "📊 Step 2: ベンチマーク実行（24条件）"
echo "========================================="

SESSION_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_NAME="auto_test"

docker exec benchmark-client bash -c "
SESSION_TIMESTAMP='$SESSION_TIMESTAMP'
SESSION_NAME='$SESSION_NAME'
SESSION_DIR=\"/app/results/session_\${SESSION_TIMESTAMP}_\${SESSION_NAME}\"
mkdir -p \"\$SESSION_DIR\"

# 新しい実験条件: 遅延0ms,20ms,40ms,60ms,80ms,100ms × 帯域幅無し,1Mbps,2Mbps,3Mbps
DELAYS=(0 20 40 60 80 100)
BANDWIDTHS=(\"0\" \"1mbit\" \"2mbit\" \"3mbit\")
BANDWIDTH_NAMES=(\"無制限\" \"1Mbps\" \"2Mbps\" \"3Mbps\")

TOTAL_CONDITIONS=\$((${#DELAYS[@]} * \${#BANDWIDTHS[@]}))

cat > \"\${SESSION_DIR}/session_info.txt\" << EOF
Session Name: \${SESSION_NAME}
Start Time: \$(date '+%Y-%m-%d %H:%M:%S')
Requests per condition: 30
Total conditions: \${TOTAL_CONDITIONS}
Delays: \${DELAYS[@]}
Bandwidths: \${BANDWIDTH_NAMES[@]}
EOF

echo \"Session directory: \$SESSION_DIR\"
echo \"Total conditions: \${TOTAL_CONDITIONS} (6 delays × 4 bandwidths)\"

current=0
for bw_idx in \"\${!BANDWIDTHS[@]}\"; do
    bandwidth=\"\${BANDWIDTHS[\$bw_idx]}\"
    bandwidth_name=\"\${BANDWIDTH_NAMES[\$bw_idx]}\"
    
    # 帯域幅ディレクトリを作成
    if [ \"\$bandwidth\" = \"0\" ]; then
        BW_DIR=\"\${SESSION_DIR}/無制限\"
    else
        BW_DIR=\"\${SESSION_DIR}/\${bandwidth_name}\"
    fi
    mkdir -p \"\${BW_DIR}/Experiment\"
    
    echo \"\"
    echo \"=========================================\"
    echo \"Bandwidth Condition: \${bandwidth_name}\"
    echo \"=========================================\"
    
    for delay in \"\${DELAYS[@]}\"; do
        current=\$((current + 1))
        exp_name=\"delay_\${delay}ms\"
        
        echo \"\"
        echo \"▶ Running experiment \$current/\${TOTAL_CONDITIONS}: delay=\${delay}ms, bandwidth=\${bandwidth_name}\"
        PARENT_SESSION_DIR=\"\$SESSION_DIR\" BANDWIDTH_DIR=\"\$BW_DIR\" DELAY_VALUE=\"\$delay\" /app/scripts/run-benchmark.sh 30 https://172.20.0.10:2000/ https://172.20.0.11:3000/ \"\$delay\" \"\$bandwidth\" \"\$exp_name\" 2>&1 | grep -E '(HTTP/[23]|TTFB|Experiment Directory|Using|Warning)'
        sleep 2
    done
done

cat >> \"\${SESSION_DIR}/session_info.txt\" << EOF
End Time: \$(date '+%Y-%m-%d %H:%M:%S')
Status: Completed
EOF

echo \"\"
echo \"✅ ベンチマーク完了!\"
echo \"Session: \$SESSION_DIR\"
"

# Step 3: グラフ生成（Docker内で実行、OS非依存）
echo ""
echo "========================================="
echo "📈 Step 3: グラフ生成（Docker内で実行）"
echo "========================================="

# Docker内でグラフ生成を実行（OS非依存）
DOCKER_SESSION_PATH="/app/results/session_${SESSION_TIMESTAMP}_${SESSION_NAME}"

echo "Docker内でグラフを生成中..."
if docker exec benchmark-client python3 /app/scripts/analyze_results.py "$DOCKER_SESSION_PATH"; then
    echo ""
    echo "========================================="
    echo "✅ すべて完了！"
    echo "========================================="
    echo ""
    
    # ホスト側のパスを表示
    HOST_SESSION_PATH="$SCRIPT_DIR/results/session_${SESSION_TIMESTAMP}_${SESSION_NAME}"
    echo "📁 結果ディレクトリ:"
    echo "   $HOST_SESSION_PATH/"
    echo ""
    echo "📊 生成されたファイル:"
    echo "   - 各帯域幅ディレクトリ（無制限/1Mbps/2Mbps/3Mbps）:"
    echo "     • summary_report.txt"
    echo "     • Experiment/response_time_comparison.png"
    echo "     • Experiment/crossover_points_summary.png"
    echo "   - ルートディレクトリ:"
    echo "     • total_report.txt"
    echo "   - analysis/ディレクトリ:"
    echo "     • ttfb_comparison.png"
    echo "     • throughput_comparison.png"
    echo "     • total_time_comparison.png"
    echo "     • summary_report.txt"
else
    echo ""
    echo "❌ グラフ生成に失敗しました"
    echo ""
    echo "トラブルシューティング:"
    echo "  1. Dockerコンテナが起動しているか確認:"
    echo "     docker ps | grep benchmark-client"
    echo ""
    echo "  2. セッションディレクトリが存在するか確認:"
    echo "     docker exec benchmark-client ls -la $DOCKER_SESSION_PATH"
    echo ""
    echo "  3. 手動でグラフを生成:"
    echo "     docker exec benchmark-client python3 /app/scripts/analyze_results.py $DOCKER_SESSION_PATH"
    echo ""
    echo "データは保存されています:"
    echo "   $SCRIPT_DIR/results/session_${SESSION_TIMESTAMP}_${SESSION_NAME}"
fi

