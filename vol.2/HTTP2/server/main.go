package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net/http"

	"seminar/vol.2/cert"
)

func main() {
	// HTTPハンドラ
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Request: %s %s (Protocol: %s)", r.Method, r.URL.Path, r.Proto)
		fmt.Fprintf(w, "Hello HTTP/2!\nProtocol: %s\n", r.Proto)
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
