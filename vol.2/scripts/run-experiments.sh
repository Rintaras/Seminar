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

# セッション情報ファイルを作成
cat > "${SESSION_DIR}/session_info.txt" << EOF
Session Name: ${SESSION_NAME}
Start Time: $(date '+%Y-%m-%d %H:%M:%S')
Requests per condition: ${NUM_REQUESTS}
Total conditions: 11
EOF

# 実験パターン定義
# [遅延(ms), 帯域幅, 実験名]
conditions=(
    "0 0 delay_0ms_bw_unlimited"        # ベースライン（理想環境・帯域無制限）
    "10 0 delay_10ms_bw_unlimited"      # 低遅延
    "50 0 delay_50ms_bw_unlimited"      # 中遅延
    "100 0 delay_100ms_bw_unlimited"    # 高遅延
    "200 0 delay_200ms_bw_unlimited"    # 非常に高い遅延
    "0 100mbit delay_0ms_bw_100mbit"    # 高速帯域
    "0 10mbit delay_0ms_bw_10mbit"      # 中速帯域
    "0 1mbit delay_0ms_bw_1mbit"        # 低速帯域
    "50 10mbit delay_50ms_bw_10mbit"    # 中遅延 + 中速帯域
    "100 10mbit delay_100ms_bw_10mbit"  # 高遅延 + 中速帯域
    "100 1mbit delay_100ms_bw_1mbit"    # 高遅延 + 低速帯域
)

total=${#conditions[@]}
current=0

for condition in "${conditions[@]}"; do
    current=$((current + 1))
    read -r delay bandwidth exp_name <<< "$condition"
    
    echo "========================================="
    echo "Experiment $current/$total: $exp_name"
    echo "  Delay: ${delay}ms, Bandwidth: ${bandwidth}"
    echo "========================================="
    
    # セッションディレクトリを環境変数で渡す
    export PARENT_SESSION_DIR="$SESSION_DIR"
    
    /app/scripts/run-benchmark.sh "$NUM_REQUESTS" \
        "https://172.20.0.10:2000/" \
        "https://172.20.0.11:3000/" \
        "$delay" \
        "$bandwidth" \
        "$exp_name"
    
    echo ""
    sleep 3
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

