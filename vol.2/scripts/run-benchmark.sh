#!/bin/bash
# ベンチマークを実行するスクリプト

set -e

# パラメータ
NUM_REQUESTS=${1:-100}
HTTP2_URL=${2:-https://172.20.0.10:2000/}
HTTP3_URL=${3:-https://172.20.0.11:3000/}
DELAY=${4:-0}
LOSS=${5:-0}

RESULTS_DIR="/app/results"
mkdir -p $RESULTS_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================="
echo "HTTP/2 vs HTTP/3 Benchmark"
echo "========================================="
echo "Requests per protocol: $NUM_REQUESTS"
echo "Network Delay: ${DELAY}ms"
echo "Network Loss: ${LOSS}%"
echo "Timestamp: $TIMESTAMP"
echo ""

# ネットワーク条件を設定
if [ "$DELAY" -gt 0 ] || [ "$LOSS" != "0" ]; then
    echo "Setting network conditions..."
    /app/scripts/set-network-conditions.sh eth0 $DELAY $LOSS
    echo ""
fi

# HTTP/2 ベンチマーク
echo "Running HTTP/2 benchmark..."
HTTP2_OUTPUT="${RESULTS_DIR}/http2_delay${DELAY}_loss${LOSS}_${TIMESTAMP}.csv"
/app/http2-benchmark \
    -url "$HTTP2_URL" \
    -n "$NUM_REQUESTS" \
    -o "$HTTP2_OUTPUT" \
    -delay "$DELAY" \
    -loss "$LOSS"

echo ""
sleep 2

# HTTP/3 ベンチマーク
echo "Running HTTP/3 benchmark..."
HTTP3_OUTPUT="${RESULTS_DIR}/http3_delay${DELAY}_loss${LOSS}_${TIMESTAMP}.csv"
/app/http3-benchmark \
    -url "$HTTP3_URL" \
    -n "$NUM_REQUESTS" \
    -o "$HTTP3_OUTPUT" \
    -delay "$DELAY" \
    -loss "$LOSS"

echo ""
echo "========================================="
echo "Benchmark completed!"
echo "Results saved to:"
echo "  HTTP/2: $HTTP2_OUTPUT"
echo "  HTTP/3: $HTTP3_OUTPUT"
echo "========================================="

# ネットワーク条件をリセット
if [ "$DELAY" -gt 0 ] || [ "$LOSS" != "0" ]; then
    echo ""
    echo "Resetting network conditions..."
    /app/scripts/reset-network-conditions.sh eth0
fi

