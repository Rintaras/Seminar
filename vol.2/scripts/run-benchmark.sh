#!/bin/bash
# ベンチマークを実行するスクリプト

set -e

# パラメータ
NUM_REQUESTS=${1:-100}
HTTP2_URL=${2:-https://172.20.0.10:2000/}
HTTP3_URL=${3:-https://172.20.0.11:3000/}
DELAY=${4:-0}
BANDWIDTH=${5:-"0"}
EXPERIMENT_NAME=${6:-"exp"}  # オプション: 実験名

# タイムスタンプとディレクトリ設定
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# セッションディレクトリが指定されていればその中に、そうでなければ独立したディレクトリに
if [ -n "$PARENT_SESSION_DIR" ]; then
    EXPERIMENT_DIR="${PARENT_SESSION_DIR}/${EXPERIMENT_NAME}"
else
    EXPERIMENT_DIR="/app/results/${TIMESTAMP}_${EXPERIMENT_NAME}_delay${DELAY}ms_bw${BANDWIDTH}"
fi

mkdir -p $EXPERIMENT_DIR

# 実験情報ファイルを作成
cat > "${EXPERIMENT_DIR}/experiment_info.txt" << EOF
Experiment Name: ${EXPERIMENT_NAME}
Timestamp: ${TIMESTAMP}
Date: $(date '+%Y-%m-%d %H:%M:%S')
---
Parameters:
  - Requests per protocol: ${NUM_REQUESTS}
  - Network Delay: ${DELAY} ms
  - Bandwidth Limit: ${BANDWIDTH}
  - HTTP/2 URL: ${HTTP2_URL}
  - HTTP/3 URL: ${HTTP3_URL}
EOF

echo "========================================="
echo "HTTP/2 vs HTTP/3 Benchmark"
echo "========================================="
echo "Requests per protocol: $NUM_REQUESTS"
echo "Network Delay: ${DELAY}ms"
echo "Bandwidth Limit: ${BANDWIDTH}"
echo "Timestamp: $TIMESTAMP"
echo ""

# ネットワーク条件を設定
if [ "$DELAY" -gt 0 ] || [ "$BANDWIDTH" != "0" ]; then
    echo "Setting network conditions..."
    /app/scripts/set-network-conditions.sh eth0 $DELAY 0 $BANDWIDTH
    echo ""
fi

# HTTP/2 ベンチマーク
echo "Running HTTP/2 benchmark..."
HTTP2_OUTPUT="${EXPERIMENT_DIR}/http2_results.csv"
/app/http2-benchmark \
    -url "$HTTP2_URL" \
    -n "$NUM_REQUESTS" \
    -o "$HTTP2_OUTPUT" \
    -delay "$DELAY" \
    -bandwidth "$BANDWIDTH"

echo ""
sleep 2

# HTTP/3 ベンチマーク
echo "Running HTTP/3 benchmark..."
HTTP3_OUTPUT="${EXPERIMENT_DIR}/http3_results.csv"
/app/http3-benchmark \
    -url "$HTTP3_URL" \
    -n "$NUM_REQUESTS" \
    -o "$HTTP3_OUTPUT" \
    -delay "$DELAY" \
    -bandwidth "$BANDWIDTH"

echo ""
echo "========================================="
echo "Benchmark completed!"
echo "Experiment Directory: $EXPERIMENT_DIR"
echo "Results saved to:"
echo "  - experiment_info.txt"
echo "  - http2_results.csv"
echo "  - http3_results.csv"
echo "========================================="

# ネットワーク条件をリセット
if [ "$DELAY" -gt 0 ] || [ "$BANDWIDTH" != "0" ]; then
    echo ""
    echo "Resetting network conditions..."
    /app/scripts/reset-network-conditions.sh eth0
fi

