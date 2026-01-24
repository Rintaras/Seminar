#!/bin/bash
# ベンチマーク動作確認スクリプト

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "🧪 ベンチマーク動作テスト"
echo "========================================="
echo ""

# Step 1: Docker確認
echo "[1/5] Docker環境の確認..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker が見つかりません"
    exit 1
fi
echo "✅ Docker: $(docker --version)"

if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon が起動していません"
    echo "    Docker Desktop を起動してください"
    exit 1
fi
echo "✅ Docker daemon が起動しています"
echo ""

# Step 2: コンテナ確認
echo "[2/5] コンテナの確認..."
if ! docker ps | grep -q "benchmark-client"; then
    echo "⚠️  benchmark-client が起動していません"
    echo "    起動しています..."
    docker-compose up -d
    sleep 5
fi
echo "✅ コンテナが起動しています:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "http|benchmark"
echo ""

# Step 3: resultsディレクトリ確認
echo "[3/5] resultsディレクトリの確認..."
mkdir -p results
echo "✅ ホスト側: $(pwd)/results"

echo "Docker内の確認:"
docker exec benchmark-client ls -ld /app/results
echo ""

# Step 4: 簡易テスト実行
echo "[4/5] 簡易ベンチマーク実行（5リクエスト）..."
TEST_DIR="test_$(date +%Y%m%d_%H%M%S)"
echo "テストディレクトリ: $TEST_DIR"
echo ""

docker exec benchmark-client bash -c "
mkdir -p /app/results/$TEST_DIR
echo 'Test started: $(date)' > /app/results/$TEST_DIR/test_info.txt
/app/http2-benchmark -url https://172.20.0.10:2000/ -n 5 -o /app/results/$TEST_DIR/http2_test.csv -delay 0 -bandwidth 0
/app/http3-benchmark -url https://172.20.0.11:3000/ -n 5 -o /app/results/$TEST_DIR/http3_test.csv -delay 0 -bandwidth 0
echo 'Test completed: $(date)' >> /app/results/$TEST_DIR/test_info.txt
ls -lh /app/results/$TEST_DIR/
"

echo ""
echo "[5/5] 結果の確認..."
sleep 2

if [ -d "results/$TEST_DIR" ]; then
    echo "✅ ホスト側にファイルが作成されました:"
    ls -lh "results/$TEST_DIR/"
    echo ""
    
    if [ -f "results/$TEST_DIR/http2_test.csv" ]; then
        echo "✅ HTTP/2 結果:"
        wc -l "results/$TEST_DIR/http2_test.csv"
        echo "   最初の3行:"
        head -3 "results/$TEST_DIR/http2_test.csv"
    else
        echo "❌ HTTP/2 CSVファイルが見つかりません"
    fi
    
    echo ""
    
    if [ -f "results/$TEST_DIR/http3_test.csv" ]; then
        echo "✅ HTTP/3 結果:"
        wc -l "results/$TEST_DIR/http3_test.csv"
        echo "   最初の3行:"
        head -3 "results/$TEST_DIR/http3_test.csv"
    else
        echo "❌ HTTP/3 CSVファイルが見つかりません"
    fi
else
    echo "❌ ホスト側にファイルが作成されませんでした"
    echo ""
    echo "Docker内の確認:"
    docker exec benchmark-client ls -la /app/results/$TEST_DIR/ 2>&1 || echo "  ディレクトリが見つかりません"
    echo ""
    echo "トラブルシューティング:"
    echo "  1. ボリュームマウントを確認:"
    echo "     docker inspect benchmark-client | grep -A5 Mounts"
    echo ""
    echo "  2. Dockerを再起動:"
    echo "     docker-compose down -v"
    echo "     docker-compose up -d"
    echo ""
    echo "  3. 権限を確認:"
    echo "     ls -ld results/"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ テスト成功！"
echo "========================================="
echo ""
echo "ベンチマークは正常に動作しています。"
echo "テスト結果: results/$TEST_DIR"
echo ""
echo "フルベンチマークを実行する場合:"
echo "  ./auto_benchmark.sh"
echo ""



