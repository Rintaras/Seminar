#!/bin/bash
# ネットワーク条件を設定するスクリプト

set -e

INTERFACE=${1:-eth0}
DELAY=${2:-0}      # 遅延（ms）
LOSS=${3:-0}       # パケット損失率（%）
BANDWIDTH=${4:-0}  # 帯域幅制限（Mbit）

echo "Setting network conditions on interface: $INTERFACE"
echo "  Delay: ${DELAY}ms"
echo "  Loss: ${LOSS}%"
echo "  Bandwidth: ${BANDWIDTH}Mbit"

# 既存のqdisc設定を削除
tc qdisc del dev $INTERFACE root 2>/dev/null || true

# 新しい設定を適用
if [ "$DELAY" -gt 0 ] || [ "$LOSS" != "0" ] || [ "$BANDWIDTH" -gt 0 ]; then
    if [ "$BANDWIDTH" -gt 0 ]; then
        # 帯域幅制限がある場合
        tc qdisc add dev $INTERFACE root handle 1: tbf rate ${BANDWIDTH}mbit burst 32kbit latency 400ms
        tc qdisc add dev $INTERFACE parent 1:1 handle 10: netem delay ${DELAY}ms loss ${LOSS}%
    else
        # 帯域幅制限がない場合
        tc qdisc add dev $INTERFACE root netem delay ${DELAY}ms loss ${LOSS}%
    fi
    echo "Network conditions applied successfully"
else
    echo "No network conditions applied (all values are 0)"
fi

# 現在の設定を表示
echo ""
echo "Current tc settings:"
tc qdisc show dev $INTERFACE

