#!/bin/bash
# 複数のネットワーク条件でベンチマークを実行するスクリプト

set -e

NUM_REQUESTS=${1:-100}

echo "Starting comprehensive benchmark experiments"
echo "Requests per condition: $NUM_REQUESTS"
echo ""

# 実験パターン定義
# [遅延(ms), パケット損失率(%)]
conditions=(
    "0 0"          # ベースライン（理想環境）
    "10 0"         # 低遅延
    "50 0"         # 中遅延
    "100 0"        # 高遅延
    "200 0"        # 非常に高い遅延
    "0 0.1"        # 低損失
    "0 1"          # 中損失
    "0 5"          # 高損失
    "50 1"         # 中遅延 + 中損失
    "100 1"        # 高遅延 + 中損失
    "100 5"        # 高遅延 + 高損失
)

total=${#conditions[@]}
current=0

for condition in "${conditions[@]}"; do
    current=$((current + 1))
    read -r delay loss <<< "$condition"
    
    echo "========================================="
    echo "Experiment $current/$total"
    echo "  Delay: ${delay}ms, Loss: ${loss}%"
    echo "========================================="
    
    /app/scripts/run-benchmark.sh "$NUM_REQUESTS" \
        "https://172.20.0.10:2000/" \
        "https://172.20.0.11:3000/" \
        "$delay" \
        "$loss"
    
    echo ""
    sleep 3
done

echo "========================================="
echo "All experiments completed!"
echo "Results are saved in /app/results/"
echo "========================================="

