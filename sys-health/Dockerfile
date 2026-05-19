FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod .
COPY . .
RUN go mod tidy && CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o sys-health .

FROM alpine:3.20
COPY --from=builder /app/sys-health /sys-health
EXPOSE 8090
ENTRYPOINT ["/sys-health"]
