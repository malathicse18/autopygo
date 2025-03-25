# Build stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

COPY go_cli/ ./

RUN go mod tidy

RUN CGO_ENABLED=0 GOOS=linux go build -o go_cli_app .

# Final stage
FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/go_cli_app ./

ENTRYPOINT ["./go_cli_app"]