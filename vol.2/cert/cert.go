package cert

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"log"
	"math/big"
	"os"
	"path/filepath"
	"time"
)

const (
	certFile = "cert.crt"
	keyFile  = "cert.key"
)

// getCertDir は証明書ディレクトリのパスを返す
func getCertDir() (string, error) {
	// 実行ファイルのディレクトリを取得
	ex, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("failed to get executable path: %w", err)
	}
	exDir := filepath.Dir(ex)

	// vol.2/certを探す
	certDir := filepath.Join(exDir, "..", "..", "cert")
	if _, err := os.Stat(certDir); err == nil {
		return certDir, nil
	}

	// カレントディレクトリから探す
	certDir = filepath.Join("vol.2", "cert")
	if _, err := os.Stat(certDir); err == nil {
		return certDir, nil
	}

	// カレントディレクトリがcertディレクトリかチェック
	if info, err := os.Stat("."); err == nil && info.IsDir() {
		if _, err := os.Stat("cert.go"); err == nil {
			return ".", nil
		}
	}

	// デフォルト（存在しなくても返す）
	return certDir, nil
}

// getCertPath は証明書ファイルのパスを返す（内部使用）
func getCertPath() (string, error) {
	dir, err := getCertDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, certFile), nil
}

// getKeyPath は秘密鍵ファイルのパスを返す（内部使用）
func getKeyPath() (string, error) {
	dir, err := getCertDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, keyFile), nil
}

// LoadOrGenerateCert は証明書をファイルから読み込むか、なければ生成して保存する
func LoadOrGenerateCert() (tls.Certificate, error) {
	certPath, err := getCertPath()
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to get cert path: %w", err)
	}
	keyPath, err := getKeyPath()
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to get key path: %w", err)
	}

	// ファイルが存在すればロード
	if _, err := os.Stat(certPath); err == nil {
		if _, err := os.Stat(keyPath); err == nil {
			log.Printf("Loading existing certificate from: %s", certPath)
			cert, err := tls.LoadX509KeyPair(certPath, keyPath)
			if err != nil {
				return tls.Certificate{}, fmt.Errorf("failed to load certificate: %w", err)
			}
			return cert, nil
		}
	}

	// 存在しなければ生成して保存
	log.Printf("Generating new certificate at: %s", certPath)
	return generateAndSaveCert(certPath, keyPath)
}

// generateAndSaveCert は証明書を生成してファイルに保存する
func generateAndSaveCert(certPath, keyPath string) (tls.Certificate, error) {
	// 秘密鍵生成
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to generate private key: %w", err)
	}

	// ランダムなシリアル番号を生成（セキュリティのため）
	serialNumberLimit := new(big.Int).Lsh(big.NewInt(1), 128)
	serialNumber, err := rand.Int(rand.Reader, serialNumberLimit)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to generate serial number: %w", err)
	}

	// 証明書テンプレート
	tmpl := &x509.Certificate{
		SerialNumber: serialNumber,
		Subject: pkix.Name{
			Organization: []string{"Development"},
			CommonName:   "localhost",
		},
		DNSNames:    []string{"localhost"},
		NotBefore:   time.Now().Add(-time.Hour),
		NotAfter:    time.Now().Add(365 * 24 * time.Hour),
		KeyUsage:    x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}

	// 証明書生成
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &priv.PublicKey, priv)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to create certificate: %w", err)
	}

	// 証明書をPEM形式でファイルに保存
	certOut, err := os.Create(certPath)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to create cert file: %w", err)
	}
	defer certOut.Close()

	if err := pem.Encode(certOut, &pem.Block{Type: "CERTIFICATE", Bytes: der}); err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to encode certificate: %w", err)
	}

	// 秘密鍵をPEM形式でファイルに保存（セキュアなパーミッション）
	keyOut, err := os.OpenFile(keyPath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to create key file: %w", err)
	}
	defer keyOut.Close()

	privBytes := x509.MarshalPKCS1PrivateKey(priv)
	if err := pem.Encode(keyOut, &pem.Block{Type: "RSA PRIVATE KEY", Bytes: privBytes}); err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to encode private key: %w", err)
	}

	log.Printf("Certificate generated successfully: %s", certPath)

	// 証明書をロードして返す
	cert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to load generated certificate: %w", err)
	}
	return cert, nil
}
