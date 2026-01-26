#!/bin/bash
# 複数のネットワーク条件でベンチマークを実行するスクリプト

set -e

NUM_REQUESTS=${1:-100}
SESSION_NAME=${2:-"comprehensive"}  # オプション: セッション名

# セッション用のタイムスタンプ
SESSION_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_DIR="/app/results/session_${SESSION_TIMESTAMP}_${SESSION_NAME}"
mkdir -p "$SESSION_DIR"

echo "========================================="
echo "Comprehensive Benchmark Experiments"
echo "========================================="
echo "Session: $SESSION_NAME"
echo "Timestamp: $SESSION_TIMESTAMP"
echo "Requests per condition: $NUM_REQUESTS"
echo "Session directory: $SESSION_DIR"
echo ""

# 遅延条件と帯域幅条件の定義
DELAYS=(0 20 40 60 80 100)
BANDWIDTHS=("0" "1mbit" "2mbit" "3mbit")
BANDWIDTH_NAMES=("無制限" "1Mbps" "2Mbps" "3Mbps")

# 総実験数を計算
TOTAL_EXPERIMENTS=$((${#DELAYS[@]} * ${#BANDWIDTHS[@]}))

# セッション情報ファイルを作成
cat > "${SESSION_DIR}/session_info.txt" << EOF
Session Name: ${SESSION_NAME}
Start Time: $(date '+%Y-%m-%d %H:%M:%S')
Requests per condition: ${NUM_REQUESTS}
Total conditions: ${TOTAL_EXPERIMENTS}
Delays: ${DELAYS[@]}
Bandwidths: ${BANDWIDTH_NAMES[@]}
EOF

current=0

# 各帯域幅条件ごとに実験を実行
for bw_idx in "${!BANDWIDTHS[@]}"; do
    bandwidth="${BANDWIDTHS[$bw_idx]}"
    bandwidth_name="${BANDWIDTH_NAMES[$bw_idx]}"
    
    # 帯域幅ディレクトリを作成
    if [ "$bandwidth" = "0" ]; then
        BW_DIR="${SESSION_DIR}/無制限"
    else
        BW_DIR="${SESSION_DIR}/${bandwidth_name}"
    fi
    mkdir -p "${BW_DIR}/Experiment"
    
    echo ""
    echo "========================================="
    echo "Bandwidth Condition: ${bandwidth_name}"
    echo "========================================="
    
    # 各遅延条件で実験を実行
    for delay in "${DELAYS[@]}"; do
        current=$((current + 1))
        
        # 実験名を生成
        if [ "$bandwidth" = "0" ]; then
            exp_name="delay_${delay}ms"
        else
            exp_name="delay_${delay}ms"
        fi
        
        echo ""
        echo "========================================="
        echo "Experiment $current/$TOTAL_EXPERIMENTS"
        echo "  Delay: ${delay}ms, Bandwidth: ${bandwidth_name}"
        echo "========================================="
        
        # セッションディレクトリと帯域幅ディレクトリを環境変数で渡す
        export PARENT_SESSION_DIR="$SESSION_DIR"
        export BANDWIDTH_DIR="$BW_DIR"
        export DELAY_VALUE="$delay"
        
        /app/scripts/run-benchmark.sh "$NUM_REQUESTS" \
            "https://172.20.0.10:2000/" \
            "https://172.20.0.11:3000/" \
            "$delay" \
            "$bandwidth" \
            "$exp_name"
        
        echo ""
        sleep 3
    done
done

# セッション完了情報を追記
cat >> "${SESSION_DIR}/session_info.txt" << EOF
End Time: $(date '+%Y-%m-%d %H:%M:%S')
Status: Completed
EOF

echo "========================================="
echo "All experiments completed!"
echo "Session directory: $SESSION_DIR"
echo ""
echo "Directory structure:"
ls -lh "$SESSION_DIR" | tail -n +2
echo "========================================="

# 自動グラフ生成
echo ""
echo "========================================="
echo "Generating analysis graphs..."
echo "========================================="

if command -v python3 &> /dev/null; then
    python3 /app/scripts/analyze_results.py "$SESSION_DIR"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================="
        echo "✅ Analysis completed successfully!"
        echo "========================================="
        echo "📊 Generated files:"
        ls -lh "${SESSION_DIR}/analysis/" 2>/dev/null | tail -n +2 || echo "  (no analysis files found)"
        echo ""
        echo "📁 Analysis directory:"
        echo "   ${SESSION_DIR}/analysis/"
        echo "========================================="
    else
        echo ""
        echo "⚠️  Analysis failed. You can run it manually:"
        echo "   python3 /app/scripts/analyze_results.py $SESSION_DIR"
    fi
else
    echo ""
    echo "⚠️  Python3 not found. Skipping analysis."
    echo "   Install Python to enable automatic graph generation."
fi

