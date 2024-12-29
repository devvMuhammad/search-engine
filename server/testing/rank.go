package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
)

// Constants for BM25 and scoring
const (
	K1               = 1.5 // Term frequency saturation parameter
	B                = 0.8 // Length normalization parameter
	ProximityBoost   = 2.0
	TitleProxBoost   = 3.0
	SafeDistanceBase = 5
	MaxSafeDistance  = 20
	TitleWeight      = 1.1
	KeywordsWeight   = 0.25
	AbstractWeight   = 0.2
)

// Document metadata structure
type Metadata struct {
	TotalDocLength  int     `json:"total_doc_length"`
	ForwardIndexLen int     `json:"forward_index_length"`
	AvgDocLength    float64 `json:"avg_doc_length"`
}

// Document posting structure
type Posting struct {
	DocID     string `json:"doc_id"`
	Frequency []int  `json:"frequency"`
	Positions []int  `json:"positions"`
	Length    int    `json:"length"`
}

// ScoredDocument for results
type ScoredDocument struct {
	DocID string
	Score float64
}

func loadMetadata() (*Metadata, error) {
	data, err := os.ReadFile("../data/metadata.json")
	if err != nil {
		return nil, err
	}

	var metadata Metadata
	if err := json.Unmarshal(data, &metadata); err != nil {
		return nil, err
	}

	metadata.AvgDocLength = float64(metadata.TotalDocLength) / float64(metadata.ForwardIndexLen)
	return &metadata, nil
}

func calculateSafeDistance(docLength int) int {
	safe := SafeDistanceBase + (docLength / 1000)
	if safe > MaxSafeDistance {
		return MaxSafeDistance
	}
	return safe
}

func calculateProximityScore(positions1, positions2 []int, safeDistance int) float64 {
	minDistance := math.MaxFloat64

	for _, pos1 := range positions1 {
		for _, pos2 := range positions2 {
			distance := math.Abs(float64(pos1 - pos2))
			if distance < minDistance {
				minDistance = distance
			}
		}
	}

	if minDistance <= float64(safeDistance) {
		return 1.0 - (minDistance / float64(safeDistance))
	}
	return 0.0
}

// BarrelMetadata maps word IDs to barrel numbers
type BarrelMetadata map[string]int

func loadBarrelMetadata() (BarrelMetadata, error) {
	data, err := os.ReadFile("../data/barrel_metadata.json")
	if err != nil {
		return nil, fmt.Errorf("failed to read barrel metadata: %v", err)
	}

	var metadata BarrelMetadata
	if err := json.Unmarshal(data, &metadata); err != nil {
		return nil, fmt.Errorf("failed to parse barrel metadata: %v", err)
	}
	return metadata, nil
}

func getDocs(barrel_number int, wordID string) ([]Posting, error) {
	data, err := os.ReadFile(fmt.Sprintf("../data/barrels/barrel_%d.json", barrel_number))
	if err != nil {
		return nil, fmt.Errorf("failed to read barrel %d: %v", barrel_number, err)
	}

	var barrel map[string][]Posting
	if err := json.Unmarshal(data, &barrel); err != nil {
		return nil, fmt.Errorf("failed to parse barrel %d: %v", barrel_number, err)
	}

	// fmt.Println("Get docs:", barrel[wordID])

	return barrel[wordID], nil
}

type Lexicon struct {
	Id        int `json:"id"`
	Frequency int `json:"frequency"`
}

func loadLexicon() map[string]Lexicon {
	data, err := os.ReadFile("../data/lexicon.json")
	if err != nil {
		return nil
	}

	var lexicon map[string]Lexicon
	if err := json.Unmarshal(data, &lexicon); err != nil {
		return nil
	}

	return lexicon
}

// query terms refer to term IDs
func calculateBM25(queryTerms []string, metadata *Metadata, barrelMetadata *BarrelMetadata) ([]ScoredDocument, []string, error) {
	start := time.Now()
	timingLogs := make([]string, 0)

	scores := make(map[string]float64)
	termPositions := make(map[string]map[string][]int)
	docLengths := make(map[string]int)

	// First pass: Basic BM25 calculation
	bm25Start := time.Now()

	for _, term := range queryTerms {

		barrel_id := (*barrelMetadata)[term]
		docs, _ := getDocs(barrel_id, term)

		if len(docs) == 0 {
			continue
		}

		df := float64(len(docs))
		idf := math.Log((float64(metadata.ForwardIndexLen)-df+0.5)/(df+0.5) + 1)

		for _, doc := range docs {
			if _, exists := termPositions[doc.DocID]; !exists {
				termPositions[doc.DocID] = make(map[string][]int)
			}
			termPositions[doc.DocID][term] = doc.Positions
			docLengths[doc.DocID] = doc.Length

			// Calculate section-weighted frequency
			f := float64(doc.Frequency[0])*TitleWeight +
				float64(doc.Frequency[1])*AbstractWeight +
				float64(doc.Frequency[2])*KeywordsWeight

			numerator := f * (K1 + 1)
			denominator := f + K1*(1-B+B*float64(doc.Length)/metadata.AvgDocLength)
			scores[doc.DocID] += idf * (numerator / denominator)
		}
	}

	timingLogs = append(timingLogs, fmt.Sprintf("BM25 calculation: %v", time.Since(bm25Start)))

	// Second pass: Proximity boost
	if len(queryTerms) >= 2 {
		proxStart := time.Now()

		for docID := range scores {
			docLength := docLengths[docID]
			safeDistance := calculateSafeDistance(docLength)
			proximityBoost := 0.0

			for i := 0; i < len(queryTerms)-1; i++ {
				for j := i + 1; j < len(queryTerms); j++ {
					term1, term2 := queryTerms[i], queryTerms[j]

					if pos1, ok1 := termPositions[docID][term1]; ok1 {
						if pos2, ok2 := termPositions[docID][term2]; ok2 {
							proxScore := calculateProximityScore(pos1, pos2, safeDistance)

							// Title proximity boost
							var titlePos1, titlePos2 []int
							for _, p := range pos1 {
								if p < 100 {
									titlePos1 = append(titlePos1, p)
								}
							}
							for _, p := range pos2 {
								if p < 100 {
									titlePos2 = append(titlePos2, p)
								}
							}

							if len(titlePos1) > 0 && len(titlePos2) > 0 {
								titleProx := calculateProximityScore(titlePos1, titlePos2, safeDistance)
								proximityBoost += titleProx * TitleProxBoost
							}

							proximityBoost += proxScore * ProximityBoost
						}
					}
				}
			}

			scores[docID] *= (1 + proximityBoost)
		}

		timingLogs = append(timingLogs, fmt.Sprintf("Proximity calculation: %v", time.Since(proxStart)))
	}

	// Convert to sorted slice
	var result []ScoredDocument
	for docID, score := range scores {
		result = append(result, ScoredDocument{DocID: docID, Score: score})
	}

	sort.Slice(result, func(i, j int) bool {
		return result[i].Score > result[j].Score
	})

	timingLogs = append(timingLogs, fmt.Sprintf("Total calculation time: %v", time.Since(start)))

	return result, timingLogs, nil
}

func main2() {
	word := "machine learning"
	wordSplit := strings.Split(word, " ")

	metadata, err := loadMetadata()
	lexicon := loadLexicon()
	documentIndex, _ := LoadIndex()

	wordIds := make([]string, 0)
	for _, w := range wordSplit {
		wordID := strconv.Itoa(lexicon[string(w)].Id)
		wordIds = append(wordIds, wordID)
	}

	barrelMetadata, err := loadBarrelMetadata()

	// Test BM25 calculation
	start := time.Now()
	scored_docs, logs, _ := calculateBM25(wordIds, metadata, &barrelMetadata)

	docIds := make([]string, 0)
	for _, doc := range scored_docs {
		docIds = append(docIds, doc.DocID)
	}

	for i, doc := range scored_docs[:10] {
		fmt.Printf("%d: %s - %f\n", i, doc.DocID, doc.Score)
	}

	for i, log := range logs {
		fmt.Printf("%d: %s\n", i, log)
	}

	elapsed := time.Since(start)
	fmt.Println("Time taken in search ", elapsed)

	docTime := time.Now()
	documentData, docError := GetDocuments("../data/test_100k.csv", docIds[:50], documentIndex)

	if docError != nil {
		fmt.Println("Error getting documents:", docError)
		return
	}

	for _, doc := range documentData {
		fmt.Println(doc.Title)
	}
	docElapsed := time.Since(docTime)
	fmt.Println("Time taken in search ", docElapsed)

	if err != nil {
		fmt.Println("Error calculating BM25:", err)
		return
	}
}
