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

	"github.com/quic-go/quic-go/http3"
)

// メモリ上に自己署名証明書を生成して返す
func generateSelfSignedCert() (tls.Certificate, error) {
	// 鍵ペア生成
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, err
	}

	// 最低限の証明書テンプレート
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

	cert := tls.Certificate{
		Certificate: [][]byte{der},
		PrivateKey:  priv,
	}
	return cert, nil
}

func main() {
	// HTTPハンドラを設定
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		isHTTP3 := r.ProtoMajor == 3
		protocol := r.Proto
		if isHTTP3 {
			protocol = "HTTP/3 (h3) 🎉"
		}

		log.Printf("Request: %s %s from %s (Protocol: %s)", r.Method, r.URL.Path, r.RemoteAddr, protocol)

		// HTTP/3が利用可能であることをブラウザに通知
		w.Header().Set("Alt-Svc", `h3=":12345"; ma=2592000`)

		fmt.Fprintf(w, "Hello from HTTP server!\n")
		fmt.Fprintf(w, "Protocol: %s\n", r.Proto)
		if isHTTP3 {
			fmt.Fprintf(w, "✅ You are connected via HTTP/3! 🎉\n")
		} else {
			fmt.Fprintf(w, "ℹ️  You are connected via %s\n", r.Proto)
			fmt.Fprintf(w, "💡 Tip: HTTP/3 is available but your browser chose %s\n", r.Proto)
		}
	})

	// 自己署名証明書を生成
	cert, err := generateSelfSignedCert()
	if err != nil {
		log.Fatal("generate cert: ", err)
	}

	// HTTP/3サーバー設定（UDP）- ポート12345
	http3Server := &http3.Server{
		Addr:    ":12345",
		Handler: handler,
		TLSConfig: &tls.Config{
			Certificates: []tls.Certificate{cert},
		},
	}

	// HTTP/2フォールバックサーバー設定（TCP）- ポート12346
	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		NextProtos:   []string{"h2", "http/1.1"},
	}

	httpServer := &http.Server{
		Addr:      ":12346",
		Handler:   handler,
		TLSConfig: tlsConfig,
	}

	// HTTP/2サーバーを別のgoroutineで起動
	go func() {
		log.Println("HTTP/2 fallback server (TCP) listening on https://localhost:12346")
		if err := httpServer.ListenAndServeTLS("", ""); err != nil {
			log.Printf("HTTP/2 server error: %v", err)
		}
	}()

	// HTTP/3サーバーを起動（メインgoroutine）
	log.Println("HTTP/3 server (UDP) listening on https://localhost:12345")
	log.Fatal(http3Server.ListenAndServe())
}
