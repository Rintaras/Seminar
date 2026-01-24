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
	// 1. Docker環境のチェック (/app/cert)
	dockerCertDir := "/app/cert"
	if info, err := os.Stat(dockerCertDir); err == nil && info.IsDir() {
		log.Printf("Found cert directory (Docker): %s", dockerCertDir)
		return dockerCertDir, nil
	}

	// 2. カレントディレクトリがcertディレクトリ自体かチェック
	if _, err := os.Stat("cert.go"); err == nil {
		return ".", nil
	}

	// 3. カレントディレクトリから上位に遡って vol.2/cert を探す
	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("failed to get current directory: %w", err)
	}

	// カレントディレクトリから最大5階層上まで探す
	dir := cwd
	for i := 0; i < 5; i++ {
		// vol.2/cert を試す
		certDir := filepath.Join(dir, "vol.2", "cert")
		if info, err := os.Stat(certDir); err == nil && info.IsDir() {
			// cert.go が存在することを確認
			if _, err := os.Stat(filepath.Join(certDir, "cert.go")); err == nil {
				log.Printf("Found cert directory: %s", certDir)
				return certDir, nil
			}
		}

		// cert ディレクトリ (vol.2直下で実行された場合)
		certDir = filepath.Join(dir, "cert")
		if info, err := os.Stat(certDir); err == nil && info.IsDir() {
			if _, err := os.Stat(filepath.Join(certDir, "cert.go")); err == nil {
				log.Printf("Found cert directory: %s", certDir)
				return certDir, nil
			}
		}

		// 一つ上のディレクトリへ
		parentDir := filepath.Dir(dir)
		if parentDir == dir {
			// ルートディレクトリに到達
			break
		}
		dir = parentDir
	}

	// 4. go run で一時ディレクトリから実行される場合のフォールバック
	// 実行ファイルのディレクトリから探す
	ex, err := os.Executable()
	if err == nil {
		exDir := filepath.Dir(ex)
		certDir := filepath.Join(exDir, "..", "..", "cert")
		if info, err := os.Stat(certDir); err == nil && info.IsDir() {
			log.Printf("Found cert directory via executable: %s", certDir)
			return certDir, nil
		}
	}

	return "", fmt.Errorf("could not find cert directory")
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
	// 証明書ディレクトリを作成
	certDir := filepath.Dir(certPath)
	if err := os.MkdirAll(certDir, 0755); err != nil {
		return tls.Certificate{}, fmt.Errorf("failed to create cert directory %s: %w", certDir, err)
	}

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
