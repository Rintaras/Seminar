package main

import (
	"bytes"
	"crypto/tls"
	"fmt"
	"log"
	"net/http"

	"seminar/vol.2/cert"
)

const (
	// レスポンスサイズ: 1MB
	responseSize = 1024 * 1024 // 1MB
)

func main() {
	// HTTPハンドラ
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Request: %s %s (Protocol: %s)", r.Method, r.URL.Path, r.Proto)
		
		// 先頭メッセージ
		message := fmt.Sprintf("Hello HTTP/2!\nProtocol: %s\n", r.Proto)
		messageBytes := []byte(message)
		
		// 1MBのデータを生成
		// メッセージ + パディングで1MBにする
		paddingSize := responseSize - len(messageBytes)
		if paddingSize < 0 {
			paddingSize = 0
		}
		
		var buf bytes.Buffer
		buf.Write(messageBytes)
		buf.Write(make([]byte, paddingSize))
		
		w.Write(buf.Bytes())
	})

	// 証明書ロードまたは生成
	certificate, err := cert.LoadOrGenerateCert()
	if err != nil {
		log.Fatal(err)
	}

	// HTTP/2サーバー設定
	server := &http.Server{
		Addr: ":2000",
		TLSConfig: &tls.Config{
			Certificates: []tls.Certificate{certificate},
			NextProtos:   []string{"h2", "http/1.1"},
		},
	}

	log.Println("HTTP/2 server listening on https://localhost:2000")
	log.Fatal(server.ListenAndServeTLS("", ""))
}
