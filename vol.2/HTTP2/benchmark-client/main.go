package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptrace"
	"time"

	"golang.org/x/net/http2"
	"seminar/vol.2/benchmark"
)

var (
	serverURL     = flag.String("url", "https://localhost:2000/", "Server URL")
	numRequests   = flag.Int("n", 100, "Number of requests")
	outputFile    = flag.String("o", "http2_results.csv", "Output CSV file")
	networkDelay  = flag.Int("delay", 0, "Network delay (ms)")
	networkLoss   = flag.Float64("loss", 0.0, "Packet loss rate (%)")
)

func main() {
	flag.Parse()

	// メトリクスコレクター初期化
	collector, err := benchmark.NewMetricsCollector(*outputFile)
	if err != nil {
		log.Fatal(err)
	}
	defer collector.Close()

	// HTTP/2クライアント作成
	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
	}
	if err := http2.ConfigureTransport(transport); err != nil {
		log.Fatal(err)
	}
	client := &http.Client{Transport: transport}

	fmt.Printf("Starting HTTP/2 benchmark...\n")
	fmt.Printf("Target: %s\n", *serverURL)
	fmt.Printf("Requests: %d\n", *numRequests)
	fmt.Printf("Network Delay: %d ms\n", *networkDelay)
	fmt.Printf("Network Loss: %.2f%%\n\n", *networkLoss)

	// 計測実行
	for i := 0; i < *numRequests; i++ {
		metrics := measureRequest(client, *serverURL)
		metrics.NetworkDelay = *networkDelay
		metrics.NetworkLoss = *networkLoss

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
	metrics.Protocol = "HTTP/2.0"
	metrics.RequestTime = time.Now()

	var firstByteTime time.Time
	startTime := time.Now()

	// httptrace でTTFBを計測
	trace := &httptrace.ClientTrace{
		GotFirstResponseByte: func() {
			firstByteTime = time.Now()
			metrics.TTFB = firstByteTime.Sub(startTime)
		},
	}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		metrics.Error = err
		return metrics
	}
	req = req.WithContext(httptrace.WithClientTrace(req.Context(), trace))

	resp, err := client.Do(req)
	if err != nil {
		metrics.Error = err
		metrics.TotalTime = time.Since(startTime)
		return metrics
	}
	defer resp.Body.Close()

	metrics.StatusCode = resp.StatusCode

	// ボディ読み取り
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		metrics.Error = err
		metrics.TotalTime = time.Since(startTime)
		return metrics
	}

	metrics.BytesReceived = int64(len(body))
	metrics.TotalTime = time.Since(startTime)

	return metrics
}

