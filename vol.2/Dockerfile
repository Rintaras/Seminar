FROM golang:1.21-alpine AS builder

# 必要なパッケージのインストール
RUN apk add --no-cache git iproute2 tc

WORKDIR /app

# Go modulesのキャッシュ
COPY go.mod go.sum ./
RUN go mod download

# ソースコードのコピー
COPY . .

# ビルド
RUN go build -o /http2-server ./vol.2/HTTP2/server/main.go
RUN go build -o /http3-server ./vol.2/HTTP3/server/main.go
RUN go build -o /http2-benchmark ./vol.2/HTTP2/benchmark-client/main.go
RUN go build -o /http3-benchmark ./vol.2/HTTP3/benchmark-client/main.go

# 実行用イメージ
FROM alpine:latest

# ネットワーク制御用ツールのインストール
RUN apk add --no-cache iproute2 iptables bash

WORKDIR /app

# ビルドしたバイナリをコピー
COPY --from=builder /http2-server /app/
COPY --from=builder /http3-server /app/
COPY --from=builder /http2-benchmark /app/
COPY --from=builder /http3-benchmark /app/

# スクリプトのコピー
COPY vol.2/scripts /app/scripts
RUN chmod +x /app/scripts/*.sh

EXPOSE 2000 3000

CMD ["/bin/bash"]

