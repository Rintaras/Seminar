#!/bin/bash
# ネットワーク条件をリセットするスクリプト

set -e

INTERFACE=${1:-eth0}

echo "Resetting network conditions on interface: $INTERFACE"

# qdisc設定を削除
tc qdisc del dev $INTERFACE root 2>/dev/null || true

echo "Network conditions reset successfully"
echo ""
echo "Current tc settings:"
tc qdisc show dev $INTERFACE

