package benchmark

import (
	"encoding/csv"
	"fmt"
	"os"
	"sync"
	"time"
)

// Metrics は性能計測結果を保持する
type Metrics struct {
	Protocol       string        // HTTP/2 or HTTP/3
	RequestTime    time.Time     // リクエスト開始時刻
	TTFB           time.Duration // Time To First Byte
	TotalTime      time.Duration // 全体の転送時間
	BytesReceived  int64         // 受信バイト数
	StatusCode     int           // HTTPステータスコード
	Error          error         // エラー（あれば）
	NetworkDelay   int           // 遅延設定 (ms)
	NetworkLoss    float64       // パケット損失率 (%)
}

// MetricsCollector は計測結果を収集する
type MetricsCollector struct {
	metrics []Metrics
	mu      sync.Mutex
	file    *os.File
	writer  *csv.Writer
}

// NewMetricsCollector は新しいコレクターを作成する
func NewMetricsCollector(filename string) (*MetricsCollector, error) {
	file, err := os.Create(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to create metrics file: %w", err)
	}

	writer := csv.NewWriter(file)
	
	// CSVヘッダーを書き込む
	header := []string{
		"Protocol",
		"RequestTime",
		"TTFB(ms)",
		"TotalTime(ms)",
		"BytesReceived",
		"StatusCode",
		"Error",
		"NetworkDelay(ms)",
		"NetworkLoss(%)",
		"Throughput(KB/s)",
	}
	if err := writer.Write(header); err != nil {
		file.Close()
		return nil, fmt.Errorf("failed to write header: %w", err)
	}
	writer.Flush()

	return &MetricsCollector{
		metrics: make([]Metrics, 0),
		file:    file,
		writer:  writer,
	}, nil
}

// Record は計測結果を記録する
func (mc *MetricsCollector) Record(m Metrics) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	mc.metrics = append(mc.metrics, m)

	// CSVに書き込む
	throughput := 0.0
	if m.TotalTime > 0 {
		throughput = float64(m.BytesReceived) / 1024.0 / m.TotalTime.Seconds()
	}

	errStr := ""
	if m.Error != nil {
		errStr = m.Error.Error()
	}

	record := []string{
		m.Protocol,
		m.RequestTime.Format(time.RFC3339Nano),
		fmt.Sprintf("%.3f", float64(m.TTFB.Microseconds())/1000.0),
		fmt.Sprintf("%.3f", float64(m.TotalTime.Microseconds())/1000.0),
		fmt.Sprintf("%d", m.BytesReceived),
		fmt.Sprintf("%d", m.StatusCode),
		errStr,
		fmt.Sprintf("%d", m.NetworkDelay),
		fmt.Sprintf("%.2f", m.NetworkLoss),
		fmt.Sprintf("%.2f", throughput),
	}

	if err := mc.writer.Write(record); err != nil {
		return fmt.Errorf("failed to write record: %w", err)
	}
	mc.writer.Flush()

	return nil
}

// GetMetrics は全ての計測結果を返す
func (mc *MetricsCollector) GetMetrics() []Metrics {
	mc.mu.Lock()
	defer mc.mu.Unlock()
	return append([]Metrics{}, mc.metrics...)
}

// Close はファイルを閉じる
func (mc *MetricsCollector) Close() error {
	if mc.writer != nil {
		mc.writer.Flush()
	}
	if mc.file != nil {
		return mc.file.Close()
	}
	return nil
}

// Summary は計測結果のサマリーを表示する
func (mc *MetricsCollector) Summary() {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if len(mc.metrics) == 0 {
		fmt.Println("No metrics recorded")
		return
	}

	// プロトコル別に集計
	stats := make(map[string]*struct {
		count       int
		totalTTFB   time.Duration
		totalTime   time.Duration
		totalBytes  int64
		minTTFB     time.Duration
		maxTTFB     time.Duration
		minTotalTime time.Duration
		maxTotalTime time.Duration
	})

	for _, m := range mc.metrics {
		if _, ok := stats[m.Protocol]; !ok {
			stats[m.Protocol] = &struct {
				count       int
				totalTTFB   time.Duration
				totalTime   time.Duration
				totalBytes  int64
				minTTFB     time.Duration
				maxTTFB     time.Duration
				minTotalTime time.Duration
				maxTotalTime time.Duration
			}{
				minTTFB:     m.TTFB,
				maxTTFB:     m.TTFB,
				minTotalTime: m.TotalTime,
				maxTotalTime: m.TotalTime,
			}
		}
		s := stats[m.Protocol]
		s.count++
		s.totalTTFB += m.TTFB
		s.totalTime += m.TotalTime
		s.totalBytes += m.BytesReceived

		if m.TTFB < s.minTTFB {
			s.minTTFB = m.TTFB
		}
		if m.TTFB > s.maxTTFB {
			s.maxTTFB = m.TTFB
		}
		if m.TotalTime < s.minTotalTime {
			s.minTotalTime = m.TotalTime
		}
		if m.TotalTime > s.maxTotalTime {
			s.maxTotalTime = m.TotalTime
		}
	}

	// サマリー表示
	fmt.Println("\n========== Performance Summary ==========")
	for protocol, s := range stats {
		avgTTFB := float64(s.totalTTFB.Microseconds()) / float64(s.count) / 1000.0
		avgTotal := float64(s.totalTime.Microseconds()) / float64(s.count) / 1000.0
		avgThroughput := float64(s.totalBytes) / 1024.0 / s.totalTime.Seconds()

		fmt.Printf("\n[%s]\n", protocol)
		fmt.Printf("  Requests:         %d\n", s.count)
		fmt.Printf("  TTFB (avg):       %.3f ms\n", avgTTFB)
		fmt.Printf("  TTFB (min/max):   %.3f / %.3f ms\n",
			float64(s.minTTFB.Microseconds())/1000.0,
			float64(s.maxTTFB.Microseconds())/1000.0)
		fmt.Printf("  Total Time (avg): %.3f ms\n", avgTotal)
		fmt.Printf("  Total Time (min/max): %.3f / %.3f ms\n",
			float64(s.minTotalTime.Microseconds())/1000.0,
			float64(s.maxTotalTime.Microseconds())/1000.0)
		fmt.Printf("  Throughput:       %.2f KB/s\n", avgThroughput)
		fmt.Printf("  Total Bytes:      %d bytes\n", s.totalBytes)
	}
	fmt.Println("==========================================\n")
}

