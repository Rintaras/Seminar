package main

import (
	"context"
	"crypto/tls"
	"log"
	"os"

	"github.com/quic-go/quic-go"
)

func main() {
	w, err := os.Create("keylog.log")
	if err != nil {
		log.Fatal("open file: ", err)
	}

	tlsConf := &tls.Config{
		InsecureSkipVerify: true,
		KeyLogWriter:       w,
	}
	quicConf := &quic.Config{}

	conn, err := quic.DialAddr(context.Background(), "127.0.0.1:12345", tlsConf, quicConf)
	if err != nil {
		log.Fatal("dial: ", err)
	}

	stream, err := conn.OpenStreamSync(context.Background())
	if err != nil {
		log.Fatal("open stream: ", err)
	}
	defer stream.Close()

	if _, err = stream.Write([]byte("Hello, golang QUIC!!\n")); err != nil {
		log.Fatal("write: ", err)
	}

	buf := make([]byte, 100)
	n, err := stream.Read(buf)
	if err != nil {
		log.Fatal("read: ", err)
	}

	log.Printf("Accept Message: `%s`", buf[:n])
}
