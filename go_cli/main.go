package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/spf13/cobra"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
)

var (
	dbName         string
	collectionName string
	mongoURL       string
)

var rootCmd = &cobra.Command{
	Use:   "gocli",
	Short: "CLI tool to fetch logs from MongoDB",
	Long:  "CLI tool to fetch logs from MongoDB",
}

var logCmd = &cobra.Command{
	Use:   "logs",
	Short: "Fetch logs from the database",
	Long:  "Fetch logs from the specified MongoDB database and collection.",
	Run: func(cmd *cobra.Command, args []string) {
		fetchLogs()
	},
}

func connectDB() (*mongo.Client, context.Context, context.CancelFunc, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURL))
	if err != nil {
		return nil, nil, nil, err
	}
	if err := client.Ping(ctx, readpref.Primary()); err != nil {
		return nil, nil, nil, fmt.Errorf("database not found")
	}
	return client, ctx, cancel, nil
}

func fetchLogs() {
	client, ctx, cancel, err := connectDB()
	if err != nil {
		log.Fatalf("Error: %v", err)
	}
	defer cancel()
	defer client.Disconnect(ctx)

	collection := client.Database(dbName).Collection(collectionName)
	cursor, err := collection.Find(ctx, bson.M{})
	if err != nil {
		log.Fatalf("Collection not found: %v", err)
	}
	defer cursor.Close(ctx)

	var logs []bson.M
	if err := cursor.All(ctx, &logs); err != nil {
		log.Fatalf("Failed to parse logs: %v", err)
	}

	if len(logs) == 0 {
		fmt.Println("No data available.")
		return
	}

	prettyLogs, err := json.MarshalIndent(logs, "", "  ")
	if err != nil {
		log.Fatalf("Failed to format logs: %v", err)
	}

	fmt.Println(string(prettyLogs))
}

func fetchLogsAPI(c *gin.Context) {
	client, ctx, cancel, err := connectDB()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer cancel()
	defer client.Disconnect(ctx)

	collection := client.Database(dbName).Collection(collectionName)
	cursor, err := collection.Find(ctx, bson.M{})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Collection not found"})
		return
	}
	defer cursor.Close(ctx)

	var logs []bson.M
	if err := cursor.All(ctx, &logs); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to parse logs"})
		return
	}

	if len(logs) == 0 {
		c.JSON(http.StatusOK, gin.H{"message": "No data available"})
		return
	}

	c.JSON(http.StatusOK, logs)
}

func startAPI() {
	r := gin.Default()
	r.GET("/logs", fetchLogsAPI)
	r.Run(":8080")
}

var apiCmd = &cobra.Command{
	Use:   "api",
	Short: "Start the log fetching API",
	Long:  "Start a RESTful API server to fetch logs from the specified MongoDB database and collection.",
	Run: func(cmd *cobra.Command, args []string) {
		startAPI()
	},
}

func main() {
	// Load environment variables from .env file
	if err := godotenv.Load(); err != nil {
		log.Fatal("Error loading .env file")
	}

	// Get values from environment variables
	mongoURL = os.Getenv("MONGO_URL")
	dbName = os.Getenv("DB_NAME")
	collectionName = os.Getenv("COLLECTION_NAME")

	rootCmd.SetHelpTemplate(`
GOCLI TOOL - Fetch from MongoDB

Usage:
  go run main.go [command]

Commands:
  api  - Start a RESTful API server to fetch logs from the specified MongoDB database and collection.

  help - Help provides help for any command in the application.
         Simply type gocli help [path to command] for full details.

  logs - Fetch logs from the specified MongoDB database and collection.

Flags:
  -h, --help   help for gocli

Example Usage:
  go run main.go logs
  go run main.go api

Use "go run main.go [command] --help" for more information about a command.
`)

	rootCmd.AddCommand(logCmd, apiCmd)
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
