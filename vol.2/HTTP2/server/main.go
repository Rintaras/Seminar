package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"log"
	"math/big"
	"net/http"
	"time"
)

// メモリ上に自己署名証明書を生成して返す
func generateSelfSignedCert() (tls.Certificate, error) {
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, err
	}

	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(365 * 24 * time.Hour),
		KeyUsage:     x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}

	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &priv.PublicKey, priv)
	if err != nil {
		return tls.Certificate{}, err
	}

	return tls.Certificate{
		Certificate: [][]byte{der},
		PrivateKey:  priv,
	}, nil
}

func main() {
	// HTTPハンドラ
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Request: %s %s (Protocol: %s)", r.Method, r.URL.Path, r.Proto)
		fmt.Fprintf(w, "Hello HTTP/2!\nProtocol: %s\n", r.Proto)
	})

	// 証明書生成
	cert, err := generateSelfSignedCert()
	if err != nil {
		log.Fatal(err)
	}

	// HTTP/2サーバー設定
	server := &http.Server{
		Addr: ":2000",
		TLSConfig: &tls.Config{
			Certificates: []tls.Certificate{cert},
			NextProtos:   []string{"h2", "http/1.1"},
		},
	}

	log.Println("HTTP/2 server listening on https://localhost:2000")
	log.Fatal(server.ListenAndServeTLS("", ""))
}
