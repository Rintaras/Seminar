package main

import (
	"crypto/tls"
	"fmt"
	"io"
	"log"
	"net/http"

	"github.com/quic-go/quic-go/http3"
)

func main() {
	// HTTP/3クライアントを作成
	roundTripper := &http3.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
	}
	defer roundTripper.Close()

	client := &http.Client{
		Transport: roundTripper,
	}

	// HTTPリクエストを送信
	resp, err := client.Get("https://localhost:12345/")
	if err != nil {
		log.Fatal("request failed: ", err)
	}
	defer resp.Body.Close()

	// レスポンスを読み取る
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatal("read response: ", err)
	}

	fmt.Printf("Status: %s\n", resp.Status)
	fmt.Printf("Protocol: %s\n", resp.Proto)
	fmt.Printf("Response:\n%s", body)
}
