#!/bin/bash
# HTTP/2サーバーの簡易テストスクリプト

URL=${1:-https://localhost:2000/}

echo "Testing HTTP/2 server at: $URL"
echo ""

go run "$(dirname "$0")/../HTTP2/client/main.go" 2>&1 | grep -A 10 "Status:"


