package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/google/uuid"
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
		word.Frequency++
		return word.Id
	} else {
		globalLexicon[wordId] = Lexicon{
			Id:        len(globalLexicon) + 1,
			Frequency: 1,
		}
		log.Println("Word not found in lexicon, adding:", wordId)
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

	log.Println("Preprocessed document:", clientDoc)
	log.Println("Preprocessed abstract:", clientDoc.Abstract)
	log.Println("Processed keywords:", processedKeywords)

	sections := []struct {
		text      string
		sectionID int
	}{
		{clientDoc.Title, 0},
		{clientDoc.Abstract, 1},
		{processedKeywords, 2},
	}

	wordData := make(map[string]struct {
		wordFreqs [3]int
		positions []int
	})
	wordFreqs := make(map[string][3]int)
	positionsDict := make(map[string][]int)

	for _, section := range sections {
		for pos, word := range strings.Split(section.text, " ") {
			termID := strconv.Itoa(updateLexicon(string(word))) // placeholder function for lexicon update

			if _, ok := wordFreqs[termID]; !ok {
				wordFreqs[termID] = [3]int{0, 0, 0}
				positionsDict[termID] = []int{}
			}
			freqEntry := wordFreqs[termID]
			freqEntry[section.sectionID]++
			wordFreqs[termID] = freqEntry

			positionsDict[termID] = append(positionsDict[termID], pos)

			wordData[termID] = struct {
				wordFreqs [3]int
				positions []int
			}{
				wordFreqs: freqEntry,
				positions: positionsDict[termID],
			}
		}
	}

	log.Println("Word frequencies:", wordFreqs)
	log.Println("Word positions:", positionsDict)
	// log.Println("Word data:", wordData)

	newDocID := "doc_" + uuid.New().String()

	// Add document to dataset and update index
	if err := appendDocumentToDataset(clientDoc, newDocID); err != nil {
		log.Printf("Error appending document: %v", err)
		return echo.NewHTTPError(http.StatusInternalServerError, "Failed to append document")
	}

	// Update barrels
	for wordId, data := range wordData {
		updateBarrel(wordId, newDocID, data)
	}

	saveAllObjects()

	return c.JSON(http.StatusOK, map[string]string{
		"message": "Document added successfully",
		"id":      newDocID,
	})
}

func saveAllObjects() error {
	var errors []string

	// Save lexicon
	lexiconBytes, err := json.MarshalIndent(globalLexicon, "", "  ")
	if err != nil {
		errors = append(errors, fmt.Sprintf("failed to marshal lexicon: %v", err))
	} else if err := os.WriteFile("../data/lexicon.json", lexiconBytes, 0644); err != nil {
		errors = append(errors, fmt.Sprintf("failed to save lexicon: %v", err))
	}

	// Save document index
	docIndexBytes, err := json.MarshalIndent(globalDocIndex, "", "  ")
	if err != nil {
		errors = append(errors, fmt.Sprintf("failed to marshal document index: %v", err))
	} else if err := os.WriteFile("../data/document_index.json", docIndexBytes, 0644); err != nil {
		errors = append(errors, fmt.Sprintf("failed to save document index: %v", err))
	}

	// Save barrel metadata
	barrelMetaBytes, err := json.MarshalIndent(globalBarrelMeta, "", "  ")
	if err != nil {
		errors = append(errors, fmt.Sprintf("failed to marshal barrel metadata: %v", err))
	} else if err := os.WriteFile("../data/barrel_metadata.json", barrelMetaBytes, 0644); err != nil {
		errors = append(errors, fmt.Sprintf("failed to save barrel metadata: %v", err))
	}

	// Save metadata
	metadataBytes, err := json.MarshalIndent(globalMetadata, "", "  ")
	if err != nil {
		errors = append(errors, fmt.Sprintf("failed to marshal metadata: %v", err))
	} else if err := os.WriteFile("../data/metadata.json", metadataBytes, 0644); err != nil {
		errors = append(errors, fmt.Sprintf("failed to save metadata: %v", err))
	}

	if len(errors) > 0 {
		return fmt.Errorf("errors saving objects: %s", strings.Join(errors, "; "))
	}
	return nil
}

type BarrelPosting struct {
	DocID     string `json:"doc_id"`
	Frequency [3]int `json:"frequency"`
	Positions []int  `json:"positions"`
}

type BarrelContent map[string][]BarrelPosting

func getFileSize(path string) (int64, error) {
	fileInfo, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return 0, nil
		}
		return 0, err
	}
	return fileInfo.Size(), nil
}

func createNewBarrel(oldBarrelId int) int {
	newBarrelId := oldBarrelId + 1
	// Update global metadata
	globalMetadata.LastBarrel = newBarrelId

	return newBarrelId
}

func updateBarrel(termId string, docId string, data struct {
	wordFreqs [3]int
	positions []int
}) error {
	const maxSize = 2 * 1024 * 1024 // 2MB in bytes

	// Create posting entry
	posting := BarrelPosting{
		DocID:     docId,
		Frequency: data.wordFreqs,
		Positions: data.positions,
	}

	// Get or assign barrel ID
	barrelId := globalBarrelMeta[termId]
	barrelPath := "../data/barrels/barrel_" + strconv.Itoa(barrelId) + ".json"

	// Check file size for new terms
	if _, exists := globalBarrelMeta[termId]; !exists {
		log.Println("Barrel for term not found, creating new:", termId)
		size, err := getFileSize(barrelPath)
		if err != nil {
			return err
		}

		if size >= maxSize {
			// Create new barrel

			lastBarrel := globalMetadata.LastBarrel

			barrelId = createNewBarrel(lastBarrel)
			log.Println("Barrel size exceeded, creating new barrel", barrelId)
			barrelPath = "../data/barrels/barrel_" + strconv.Itoa(barrelId) + ".json"
		}

		// Update barrel metadata

		log.Println("Updating barrel metadata:", termId, barrelId)
		globalBarrelMeta[termId] = barrelId
		// if err := saveBarrelMetadata(); err != nil {
		// 	return fmt.Errorf("failed to save barrel metadata: %v", err)
		// }
	}

	// Read existing barrel content or create new
	var barrelContent BarrelContent
	if fileBytes, err := os.ReadFile(barrelPath); err == nil {
		if err := json.Unmarshal(fileBytes, &barrelContent); err != nil {
			barrelContent = make(BarrelContent)
		}
	} else {
		barrelContent = make(BarrelContent)
	}

	// Update barrel content
	log.Println("Updating barrel content:", barrelPath)
	if _, exists := barrelContent[termId]; !exists {
		barrelContent[termId] = []BarrelPosting{}
	}
	barrelContent[termId] = append(barrelContent[termId], posting)

	// Write updated content
	updatedContent, err := json.MarshalIndent(barrelContent, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal barrel content: %v", err)
	}

	globalMetadata.LastBarrel = barrelId

	log.Println("Updated Barrel Successfully!", barrelPath)
	return os.WriteFile(barrelPath, updatedContent, 0644)
}

func saveBarrelMetadata() error {
	metadataBytes, err := json.MarshalIndent(globalMetadata, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile("../data/barrel_metadata.json", metadataBytes, 0644)
}

func generateUUID() string {
	// Minimal placeholder or use "github.com/google/uuid"
	return "12345678-1234-5678-1234-567812345678"
}

func jsonify(arr []string) string {
	bytes, _ := json.Marshal(arr)
	return string(bytes)
}

func appendDocumentToDataset(doc ClientDocumentType, docId string) error {
	// Open file in append mode
	file, err := os.OpenFile("../data/test_100k.csv", os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open dataset file: %v", err)
	}
	defer file.Close()

	// Get current offset for document index
	offset, err := file.Seek(0, io.SeekEnd)
	if err != nil {
		return fmt.Errorf("failed to get file offset: %v", err)
	}

	// // Convert authors to string format
	authorStrs := make([]string, len(doc.Authors))
	for i, author := range doc.Authors {
		authorBytes, _ := json.Marshal(author)
		authorStrs[i] = string(authorBytes)
	}
	authors := jsonify(authorStrs)

	// Convert venue map to string
	venueBytes, _ := json.Marshal(doc.Venue)
	venue := string(venueBytes)

	// jsonify keywords

	// Create CSV writer
	writer := csv.NewWriter(file)

	// Prepare record
	record := []string{
		docId,                       // id
		doc.Title,                   // title
		jsonify(doc.Keywords),       // keywords
		venue,                       // venue
		strconv.Itoa(doc.Year),      // year
		strconv.Itoa(doc.NCitation), // n_citation
		jsonify(doc.URL),            // url
		doc.Abstract,                // abstract
		authors,                     // authors
		doc.DocType,                 // doc_type
		jsonify(doc.References),     // references
	}

	// Write record
	if err := writer.Write(record); err != nil {
		return fmt.Errorf("failed to write record: %v", err)
	}
	writer.Flush()

	if err := writer.Error(); err != nil {
		return fmt.Errorf("error flushing writer: %v", err)
	}

	// Update document index
	globalDocIndex[docId] = offset

	globalMetadata.ForwardIndexLen += 1
	globalMetadata.TotalDocLength += 1
	globalMetadata.AvgDocLength = float64(globalMetadata.TotalDocLength) / float64(globalMetadata.ForwardIndexLen)

	return nil
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
