package main

import (
	"encoding/json"
	"io"
	"log"
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

type Author struct {
	Id   string `json:"id"`
	Name string `json:"name"`
	Org  string `json:"org"`
}

type ClientDocumentType struct {
	Title      string            `json:"title"`
	Keywords   []string          `json:"keywords"`
	Venue      map[string]string `json:"venue"`
	Year       int               `json:"year"`
	NCitation  int               `json:"n_citation"`
	URL        []string          `json:"url"`
	Abstract   string            `json:"abstract"`
	Authors    []Author          `json:"authors"`
	DocType    string            `json:"doc_type"`
	References []string          `json:"references"`
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

func updateLexicon(wordId string) int {
	if word, ok := globalLexicon[wordId]; ok {
		// Placeholder for updating lexicon
		log.Println("Word not found in lexicon, adding:", wordId)
		return word.Id
	} else {
		globalLexicon[wordId] = Lexicon{
			Id:        len(globalLexicon) + 1,
			Frequency: 1,
		}
		return globalLexicon[wordId].Id
	}
}

func addHandler(c echo.Context) error {
	b, _ := io.ReadAll(c.Request().Body)

	// 1. Parse the request body
	var clientDoc ClientDocumentType
	if err := json.Unmarshal(b, &clientDoc); err != nil {
		log.Println(err.Error())
		return err
	}

	// 2. Preprocess the document (request to python API)
	preprocessURL := "http://127.0.0.1:5000/preprocess" // adjust if needed
	preData, _ := json.Marshal(clientDoc)
	req, err := http.NewRequest("POST", preprocessURL, strings.NewReader(string(preData)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Println("Error calling /preprocess:", err)
		return err
	}
	defer resp.Body.Close()

	var preprocessed map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&preprocessed); err != nil {
		log.Println("Error decoding /preprocess response:", err)
		return err
	}
	if !preprocessed["success"].(bool) {
		log.Println("Preprocess failed:", preprocessed["error"])
		return echo.NewHTTPError(http.StatusBadRequest, "Preprocessing failed")
	}
	// Update the doc fields
	clientDoc.Title = preprocessed["title"].(string)
	clientDoc.Abstract = preprocessed["abstract"].(string)
	processedKeywords := preprocessed["keywords"].(string)

	sections := []struct {
		text      string
		sectionID int
	}{
		{clientDoc.Title, 0},
		{clientDoc.Abstract, 1},
		{processedKeywords, 2},
	}

	wordFreqs := make(map[string][3]int)
	positionsDict := make(map[string][]int)

	for _, section := range sections {
		for pos, word := range section.text {
			termID := strconv.Itoa(updateLexicon(string(word))) // placeholder function for lexicon update

			if _, ok := wordFreqs[termID]; !ok {
				wordFreqs[termID] = [3]int{0, 0, 0}
				positionsDict[termID] = []int{}
			}
			freqEntry := wordFreqs[termID]
			freqEntry[section.sectionID]++
			wordFreqs[termID] = freqEntry

			positionsDict[termID] = append(positionsDict[termID], pos)
		}
	}

	log.Println("Word frequencies:", wordFreqs)
	log.Println("Word positions:", positionsDict)

	// 3. Update the lexicon (updates the lexicon file as well)

	// 4. Update the barrel (updates the barrel_metadata as well)
	// (Mocked sample, adapt as needed)
	if err := updateBarrelsWithDoc(clientDoc); err != nil {
		log.Println("Error updating barrel:", err)
		return err
	}

	// 5. Add the document to the dataset file (append at end)
	newDocID := "doc_" + generateUUID()
	if err := appendDocumentToCSV(newDocID, &clientDoc); err != nil {
		log.Println("Error appending to dataset:", err)
		return err
	}

	// 6. Update the document index
	if err := updateDocumentIndex(newDocID, globalDocIndex); err != nil {
		log.Println("Error updating doc index:", err)
		return err
	}

	return c.JSON(http.StatusOK, map[string]string{
		"message": "Document added successfully",
	})
}

func updateBarrelsWithDoc(doc ClientDocumentType) error {
	// Example placeholder for updating barrels
	return nil
}

func appendDocumentToCSV(docID string, doc *ClientDocumentType) error {
	// Example placeholder for appending row
	// e.g. open file, write CSV line, close
	return nil
}

func updateDocumentIndex(docID string, index map[string]int64) error {
	// Example placeholder for updating the in-memory/disk index
	return nil
}

func generateUUID() string {
	// Minimal placeholder or use "github.com/google/uuid"
	return "12345678-1234-5678-1234-567812345678"
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
	e.POST("/add", addHandler)

	// Start server
	e.Logger.Fatal(e.Start(":4000"))
}
