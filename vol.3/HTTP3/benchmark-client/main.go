package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"seminar/vol.2/benchmark"

	"github.com/quic-go/quic-go"
	"github.com/quic-go/quic-go/http3"
)

var (
	serverURL    = flag.String("url", "https://localhost:3000/", "Server URL")
	numRequests  = flag.Int("n", 100, "Number of requests")
	outputFile   = flag.String("o", "http3_results.csv", "Output CSV file")
	networkDelay = flag.Int("delay", 0, "Network delay (ms)")
	bandwidth    = flag.String("bandwidth", "0", "Bandwidth limit (e.g., 1mbit, 10mbit, 100mbit)")
)

func main() {
	flag.Parse()

	// メトリクスコレクター初期化
	collector, err := benchmark.NewMetricsCollector(*outputFile)
	if err != nil {
		log.Fatal(err)
	}
	defer collector.Close()

	// HTTP/3クライアント作成（接続再利用とQUIC設定を最適化）
	transport := &http3.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
		// 接続の再利用を明示的に有効化
		DisableCompression: false,
		// QUIC設定の最適化（帯域制限下での性能向上）
		QUICConfig: &quic.Config{
			// 接続のアイドルタイムアウトを延長（接続再利用を促進）
			MaxIdleTimeout: 30 * time.Second,
			// 輻輳制御アルゴリズムの最適化
			// デフォルトのCubicを使用（帯域制限下でも効率的）
		},
	}
	defer transport.Close()

	client := &http.Client{
		Transport: transport,
		// タイムアウト設定
		Timeout: 30 * time.Second,
	}

	fmt.Printf("Starting HTTP/3 benchmark...\n")
	fmt.Printf("Target: %s\n", *serverURL)
	fmt.Printf("Requests: %d\n", *numRequests)
	fmt.Printf("Network Delay: %d ms\n", *networkDelay)
	fmt.Printf("Bandwidth Limit: %s\n\n", *bandwidth)

	// 計測実行
	for i := 0; i < *numRequests; i++ {
		metrics := measureRequest(client, *serverURL)
		metrics.NetworkDelay = *networkDelay
		metrics.Bandwidth = *bandwidth

		if err := collector.Record(metrics); err != nil {
			log.Printf("Failed to record metrics: %v", err)
		}

		// 進捗表示
		if (i+1)%10 == 0 {
			fmt.Printf("Progress: %d/%d requests completed\n", i+1, *numRequests)
		}

		// 少し待機（サーバー負荷軽減）
		time.Sleep(10 * time.Millisecond)
	}

	// サマリー表示
	collector.Summary()
	fmt.Printf("Results saved to: %s\n", *outputFile)
}

func measureRequest(client *http.Client, url string) benchmark.Metrics {
	var metrics benchmark.Metrics
	metrics.Protocol = "HTTP/3.0"
	metrics.RequestTime = time.Now()

	startTime := time.Now()

	resp, err := client.Get(url)
	if err != nil {
		metrics.Error = err
		metrics.TotalTime = time.Since(startTime)
		return metrics
	}
	defer resp.Body.Close()

	// 最初の1バイトを読んでTTFBを計測
	firstByte := make([]byte, 1)
	_, err = resp.Body.Read(firstByte)
	if err != nil && err != io.EOF {
		metrics.Error = err
		metrics.TotalTime = time.Since(startTime)
		return metrics
	}
	metrics.TTFB = time.Since(startTime)

	metrics.StatusCode = resp.StatusCode

	// 残りのボディを読み取り
	restBody, err := io.ReadAll(resp.Body)
	if err != nil {
		metrics.Error = err
		metrics.TotalTime = time.Since(startTime)
		return metrics
	}

	metrics.BytesReceived = int64(len(firstByte) + len(restBody))
	metrics.TotalTime = time.Since(startTime)

	return metrics
}
