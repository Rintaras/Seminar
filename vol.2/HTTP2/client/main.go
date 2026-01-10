package main

import (
	"crypto/tls"
	"fmt"
	"io"
	"log"
	"net/http"

	"golang.org/x/net/http2"
)

func main() {
	// HTTP/2クライアント
	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
	}

	// HTTP/2を有効化
	if err := http2.ConfigureTransport(transport); err != nil {
		log.Fatal(err)
	}

	client := &http.Client{Transport: transport}

	// リクエスト送信
	resp, err := client.Get("https://localhost:2000/")
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	// レスポンス読み取り
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Status: %s\n", resp.Status)
	fmt.Printf("Protocol: %s\n", resp.Proto)
	fmt.Printf("Response:\n%s", body)
}
