package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"
)

type LexiconEntry struct {
	ID        int `json:"id"`
	Frequency int `json:"frequency"`
}

type Lexicon map[string]LexiconEntry

func loadLexicon() (Lexicon, error) {
	lexiconPath := "../server/data/lexicon.json"
	data, err := os.ReadFile(lexiconPath)
	if err != nil {
		return nil, err
	}

	var lexicon Lexicon
	if err := json.Unmarshal(data, &lexicon); err != nil {
		return nil, err
	}
	return lexicon, nil
}

type WordInfo struct {
	Frequency []int `json:"frequency"`
	Positions []int `json:"positions"`
}

func loadForwardIndex(path string) (map[string]map[string]WordInfo, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var forwardIndex map[string]map[string]WordInfo
	if err := json.Unmarshal(data, &forwardIndex); err != nil {
		return nil, err
	}
	return forwardIndex, nil
}

func buildForwardIndex() map[string]map[string]WordInfo {
	inputFile := "../server/data/preprocessed_test_100k.csv"
	forwardIndexPath := "../server/data/test_forward_index.json"

	file, err := os.Open(inputFile)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}

	headers := records[0]
	idIdx := indexOf(headers, "id")
	titleIdx := indexOf(headers, "title")
	abstractIdx := indexOf(headers, "abstract")
	keywordsIdx := indexOf(headers, "keywords")

	lexicon, err := loadLexicon()
	if err != nil {
		panic(err)
	}

	forwardIndex := make(map[string]map[string]WordInfo)
	totalDocLength := 0

	for _, record := range records[1:] {
		docID := record[idIdx]
		title := strings.Split(getOrEmpty(record, titleIdx), " ")
		abstract := strings.Split(getOrEmpty(record, abstractIdx), " ")
		keywords := strings.Split(getOrEmpty(record, keywordsIdx), " ")

		totalLength := len(title) + len(abstract)
		sections := []struct {
			words []string
			index int
		}{
			{title, 0},
			{abstract, 1},
			{keywords, 2},
		}

		wordDict := make(map[string]WordInfo)
		basePosition := 0

		for _, section := range sections {
			for pos, word := range section.words {
				if wordID, exists := lexicon[word]; exists {
					info, exists := wordDict[string(rune(wordID.ID))]
					if !exists {
						info = WordInfo{
							Frequency: []int{0, 0, 0},
							Positions: []int{},
						}
					}
					info.Positions = append(info.Positions, basePosition+pos)
					info.Frequency[section.index]++
					wordDict[string(rune(wordID.ID))] = info
				}
			}
			basePosition += len(section.words)
		}

		forwardIndex[docID] = wordDict
		totalDocLength += totalLength
	}

	saveForwardIndex(forwardIndex, forwardIndexPath)
	saveMetadata(totalDocLength, len(forwardIndex))

	return forwardIndex
}

func saveForwardIndex(index map[string]map[string]WordInfo, path string) {
	data, err := json.MarshalIndent(index, "", "  ")
	if err != nil {
		panic(err)
	}
	if err := os.WriteFile(path, data, 0644); err != nil {
		panic(err)
	}
	fmt.Printf("Forward index saved to %s\n", path)
}

func saveMetadata(totalDocLength, indexLength int) {
	metadata := struct {
		TotalDocLength     int `json:"total_doc_length"`
		ForwardIndexLength int `json:"forward_index_length"`
	}{
		TotalDocLength:     totalDocLength,
		ForwardIndexLength: indexLength,
	}

	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		panic(err)
	}
	if err := os.WriteFile("../server/data/metadata.json", data, 0644); err != nil {
		panic(err)
	}
	fmt.Println("Metadata saved to ../server/data/metadata.json")
}

func main() {
	startTime := time.Now()
	buildForwardIndex()
	elapsed := time.Since(startTime)
	fmt.Printf("Forward Index built in %v seconds\n", elapsed.Seconds())
}

// Helper functions remain the same
func indexOf(slice []string, item string) int {
	for i, s := range slice {
		if s == item {
			return i
		}
	}
	return -1
}

func getOrEmpty(slice []string, index int) string {
	if index >= 0 && index < len(slice) {
		if slice[index] == "" {
			return ""
		}
		return slice[index]
	}
	return ""
}
