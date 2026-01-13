#!/bin/bash
# HTTP/3サーバーの簡易テストスクリプト

URL=${1:-https://localhost:3000/}

echo "Testing HTTP/3 server at: $URL"
echo ""

go run "$(dirname "$0")/../HTTP3/client/main.go" 2>&1 | grep -A 10 "Status:"


