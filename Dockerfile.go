# Use the official Golang image as the base image
FROM golang:1.22 

# Set the working directory inside the container
WORKDIR /app

# Copy the Go CLI source code
COPY go_cli/ ./go_cli

# Build the Go application
RUN cd go_cli && go build -o go_cli .

# Set the entry point for the Go CLI
ENTRYPOINT ["./go_cli/go_cli"]