FROM golang:1.26.3

WORKDIR /app

COPY go.mod go.sum ./

RUN go mod download

RUN adduser --disabled-password appuser

COPY . .

RUN chown -R appuser:appuser /app

RUN CGO_ENABLED=0 GOOS=linux go build -o /core-api ./cmd/app/main.go

USER appuser

CMD ["/core-api"]