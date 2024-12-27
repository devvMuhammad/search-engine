package main

import (
	"encoding/csv"
	"encoding/json"
	"io"
	"os"
)

type Document struct {
	ID         string `json:"id"`
	Title      string `json:"title"`
	Keywords   string `json:"keywords"`
	Venue      string `json:"venue"`
	Year       string `json:"year"`
	NCitation  string `json:"n_citation"`
	URL        string `json:"url"`
	Abstract   string `json:"abstract"`
	Authors    string `json:"authors"`
	DocType    string `json:"doc_type"`
	References string `json:"references"`
}

// loadIndex loads document offsets from JSON file
func LoadIndex() (map[string]int64, error) {
	data, err := os.ReadFile("../data/document_index.json")
	if err != nil {
		return nil, err
	}

	var index map[string]int64
	if err := json.Unmarshal(data, &index); err != nil {
		return nil, err
	}

	return index, nil
}

// getDocuments retrieves documents by their IDs
func GetDocuments(csvPath string, docIDs []string, index map[string]int64) ([]*Document, error) {
	file, err := os.Open(csvPath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	results := make([]*Document, len(docIDs))

	for i, docID := range docIDs {
		offset, exists := index[docID]
		if !exists {
			results[i] = nil
			continue
		}

		if _, err := file.Seek(offset, 0); err != nil {
			return nil, err
		}

		reader := csv.NewReader(file)
		record, err := reader.Read()
		if err != nil {
			if err == io.EOF {
				results[i] = nil
				continue
			}
			return nil, err
		}

		results[i] = &Document{
			ID:         record[0],
			Title:      record[1],
			Keywords:   record[2],
			Venue:      record[3],
			Year:       record[4],
			NCitation:  record[5],
			URL:        record[6],
			Abstract:   record[7],
			Authors:    record[8],
			DocType:    record[9],
			References: record[10],
		}
	}

	return results, nil
}

func main1() {
	// indexPath := "../data/document_index.json"
	csvPath := "../data/test_100k.csv"
	docIDs := []string{"1", "2", "3", "4", "5"}
	documentIndex, err := LoadIndex()

	docs, err := GetDocuments(csvPath, docIDs, documentIndex)
	if err != nil {
		panic(err)
	}

	for _, doc := range docs {
		if doc != nil {
			println(doc.ID)
		}
	}
}
