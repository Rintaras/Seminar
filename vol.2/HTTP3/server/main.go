package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net/http"

	"seminar/vol.2/cert"

	"github.com/quic-go/quic-go/http3"
)

func main() {
	// HTTPハンドラ
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Request: %s %s (Protocol: %s)", r.Method, r.URL.Path, r.Proto)
		fmt.Fprintf(w, "Hello HTTP/3!\nProtocol: %s\n", r.Proto)
	})

	// 証明書ロードまたは生成
	certificate, err := cert.LoadOrGenerateCert()
	if err != nil {
		log.Fatal(err)
	}

	// HTTP/3サーバー設定
	server := &http3.Server{
		Addr:    ":3000",
		Handler: nil, // DefaultServeMuxを使用
		TLSConfig: &tls.Config{
			Certificates: []tls.Certificate{certificate},
		},
	}

	log.Println("HTTP/3 server listening on https://localhost:3000")
	log.Fatal(server.ListenAndServe())
}
