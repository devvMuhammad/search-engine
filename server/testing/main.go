package main

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

// Global variables to store loaded data
var (
	globalMetadata   *Metadata
	globalLexicon    map[string]Lexicon
	globalDocIndex   map[string]int64
	globalBarrelMeta BarrelMetadata
)

type SearchResponse struct {
	Query        string      `json:"query"`
	Results      []*Document `json:"results"`
	ResultsCount int         `json:"results_count"`
}

func initializeData() error {
	var err error

	// Load metadata
	globalMetadata, err = loadMetadata()
	if err != nil {
		return err
	}

	// Load lexicon
	globalLexicon = loadLexicon()
	if globalLexicon == nil {
		return echo.NewHTTPError(http.StatusInternalServerError, "Failed to load lexicon")
	}

	// Load document index
	globalDocIndex, err = LoadIndex()
	if err != nil {
		return err
	}

	// Load barrel metadata
	globalBarrelMeta, err = loadBarrelMetadata()
	if err != nil {
		return err
	}

	return nil
}

func searchHandler(c echo.Context) error {
	query := c.QueryParam("q")
	if query == "" {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Query parameter 'q' is required",
		})
	}

	// Split query into words
	wordSplit := strings.Split(query, " ")

	// Convert words to IDs
	wordIds := make([]string, 0)
	for _, w := range wordSplit {
		if lex, ok := globalLexicon[w]; ok {
			wordID := strconv.Itoa(lex.Id)
			wordIds = append(wordIds, wordID)
		}
	}

	// Calculate BM25 scores
	scoredDocs, _, err := calculateBM25(wordIds, globalMetadata, &globalBarrelMeta)
	if err != nil {
		return echo.NewHTTPError(http.StatusInternalServerError, err.Error())
	}

	// Get document IDs
	docIds := make([]string, 0)
	for _, doc := range scoredDocs {
		docIds = append(docIds, doc.DocID)
	}

	// Limit to top 50 documents
	limit := 50
	if len(docIds) > limit {
		docIds = docIds[:limit]
	}

	// Fetch document details
	documents, err := GetDocuments("../data/test_100k.csv", docIds, globalDocIndex)
	if err != nil {
		return echo.NewHTTPError(http.StatusInternalServerError, err.Error())
	}

	response := SearchResponse{
		Results:      documents,
		ResultsCount: len(documents),
		Query:        strings.Join(wordSplit, " "),
	}

	return c.JSON(http.StatusOK, response)
}

func main() {
	// Initialize Echo
	e := echo.New()

	// Middleware
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	e.Use(middleware.CORS())

	// Initialize data
	if err := initializeData(); err != nil {
		e.Logger.Fatal("Failed to initialize data:", err)
	}

	// Routes
	e.GET("/search", searchHandler)

	// Start server
	e.Logger.Fatal(e.Start(":4000"))
}
