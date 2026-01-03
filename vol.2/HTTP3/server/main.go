package main

import (
	"bufio"
	"context"
	"crypto/tls"
	"log"

	"github.com/quic-go/quic-go"
)

func main() {
	cer, err := tls.LoadX509KeyPair("server.crt", "server.key")
	if err != nil {
		log.Fatal("loadkeys: ", err)
	}

	tlsConf := &tls.Config{Certificates: []tls.Certificate{cer}}
	quicConf := &quic.Config{}

	ln, err := quic.ListenAddr("127.0.0.1:12345", tlsConf, quicConf)
	if err != nil {
		log.Fatal("listen addr: ", err)
	}
	defer ln.Close()

	log.Print("Start Server:")

	for {
		conn, err := ln.Accept(context.Background())
		if err != nil {
			log.Fatal("accept: ", err)
		}

		stream, err := conn.AcceptStream(context.Background())
		if err != nil {
			log.Fatal("accept stream: ", err)
		}

		log.Print("New Client Connection Accepted")
		go func(stream quic.Stream) {
			s := bufio.NewScanner(stream)
			for s.Scan() {
				msg := s.Text()
				log.Printf("Accept Message: `%s`", msg)
				_, err := stream.Write([]byte(msg))
				if err != nil {
					log.Print("write: ", err)
				}
			}
		}(stream)
	}
}
