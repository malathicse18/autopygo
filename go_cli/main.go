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
	"github.com/spf13/cobra"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var (
	dbName         string
	collectionName string
)

// Root command with improved description
var rootCmd = &cobra.Command{
	Use:   "gocli",
	Short: "CLI tool to fetch logs from MongoDB",
	Long: `A command-line tool to fetch logs from a MongoDB database.

Available commands:
  logs  - Fetch logs from MongoDB using CLI
  api   - Start an API server to fetch logs via HTTP requests

Example Usage:
  Fetch logs via CLI:
    gocli logs --db=myDatabase --collection=myCollection
  
  Start API server:
    gocli api
  
  Fetch logs via API:
    curl "http://localhost:8080/logs?db=myDatabase&collection=myCollection"
  `,
}

// Log command with example usage
var logCmd = &cobra.Command{
	Use:   "logs",
	Short: "Fetch logs from the specified MongoDB database and collection",
	Long: `Fetch logs from MongoDB.

Example:
  gocli logs --db=myDatabase --collection=myCollection`,
	Run: func(cmd *cobra.Command, args []string) {
		if dbName == "" || collectionName == "" {
			fmt.Println("Error: --db and --collection flags are required.")
			fmt.Println("Usage: gocli logs --db=myDatabase --collection=myCollection")
			os.Exit(1)
		}
		fetchLogs()
	},
}

func connectDB() (*mongo.Client, context.Context, context.CancelFunc) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	client, err := mongo.Connect(ctx, options.Client().ApplyURI("mongodb://localhost:27017"))
	if err != nil {
		log.Fatal(err)
	}
	return client, ctx, cancel
}

func fetchLogs() {
	client, ctx, cancel := connectDB()
	defer cancel()
	defer client.Disconnect(ctx)

	collection := client.Database(dbName).Collection(collectionName)
	cursor, err := collection.Find(ctx, bson.M{})
	if err != nil {
		log.Fatal(err)
	}
	defer cursor.Close(ctx)

	var logs []bson.M
	if err := cursor.All(ctx, &logs); err != nil {
		log.Fatal(err)
	}

	prettyLogs, err := json.MarshalIndent(logs, "", "  ")
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(string(prettyLogs))
}

// API handler for fetching logs
func fetchLogsAPI(c *gin.Context) {
	dbName := c.Query("db")                 // Get DB name from query params
	collectionName := c.Query("collection") // Get Collection name from query params

	if dbName == "" || collectionName == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing db or collection parameter. Usage: /logs?db=myDatabase&collection=myCollection"})
		return
	}

	client, ctx, cancel := connectDB()
	defer cancel()
	defer client.Disconnect(ctx)

	collection := client.Database(dbName).Collection(collectionName)
	cursor, err := collection.Find(ctx, bson.M{})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer cursor.Close(ctx)

	var logs []bson.M
	if err := cursor.All(ctx, &logs); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, logs)
}

func startAPI() {
	r := gin.Default()
	r.GET("/logs", fetchLogsAPI) // API now supports dynamic DB & Collection selection
	r.Run(":8080")
}

// API command with example usage
var apiCmd = &cobra.Command{
	Use:   "api",
	Short: "Start the log fetching API",
	Long: `Start an API server to fetch logs via HTTP requests.

Example:
  gocli api
  curl "http://localhost:8080/logs?db=myDatabase&collection=myCollection"`,
	Run: func(cmd *cobra.Command, args []string) {
		startAPI()
	},
}

func main() {
	rootCmd.PersistentFlags().StringVar(&dbName, "db", "", "Database name (required for logs command)")
	rootCmd.PersistentFlags().StringVar(&collectionName, "collection", "", "Collection name (required for logs command)")

	rootCmd.AddCommand(logCmd, apiCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
