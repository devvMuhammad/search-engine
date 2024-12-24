import json
from collections import defaultdict
import math
import time
from server.entities.lexicon import Lexicon
from server.entities.barrels import Barrels
from server.entities.docindex import DocumentIndex

# BM25 parameters
k1 = 1.5  # Term frequency saturation parameter
b = 0.8   # Length normalization parameter

# Section and proximity weights
PROXIMITY_BOOST = 2.0
TITLE_PROXIMITY_BOOST = 3.0
SAFE_DISTANCE_BASE = 5
MAX_SAFE_DISTANCE = 20
TITLE_WEIGHT = 1.1
KEYWORDS_WEIGHT = 0.25
ABSTRACT_WEIGHT = 0.2

# Load lexicon
start = time.time()
lexicon = Lexicon().lexicon
end = time.time()
print("time for loading lexicon: ", end - start)

def load_document_metadata():
    try:
        with open("server/data/metadata.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception("Required metadata.json file not found")

def calculate_safe_distance(doc_length):
    """Calculate safe distance based on document length"""
    return min(SAFE_DISTANCE_BASE + (doc_length // 1000), MAX_SAFE_DISTANCE)

def calculate_proximity_score(positions1, positions2, safe_distance):
    """Calculate proximity score between two terms"""
    min_distance = float('inf')
    for pos1 in positions1:
        for pos2 in positions2:
            distance = abs(pos1 - pos2)
            min_distance = min(min_distance, distance)
    
    if min_distance <= safe_distance:
        return 1.0 - (min_distance / safe_distance)
    return 0.0

def calculate_bm25(query_terms):
    timing_logs = []
    total_start = time.time()
    
    N = forward_index_length
    bm25_scores = defaultdict(float)
    term_positions = defaultdict(lambda: defaultdict(list))
    doc_lengths = {}  # Store doc lengths from barrel entries
    
    barrel_start = time.time()
    barrels_obj = Barrels()
    timing_logs.append(f"Barrel initialization: {time.time() - barrel_start:.4f} seconds")

    # First pass: Basic BM25 calculation and position collection
    for term in query_terms:
        if term not in lexicon:
            continue
            
        word_id = str(lexicon[term]["id"])
        docs = barrels_obj.load_barrel(term)
        
        if not docs:
            continue

        df = len(docs)
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

        for doc in docs:
            doc_id = doc["doc_id"]
            term_positions[doc_id][term].extend(doc.get("positions", []))
            doc_lengths[doc_id] = doc.get("doc_length", avg_doc_length)  # Get doc length from barrel
            
            # Calculate section-weighted frequency
            f = (
                doc["frequency"][0] * TITLE_WEIGHT +
                doc["frequency"][1] * ABSTRACT_WEIGHT +
                doc["frequency"][2] * KEYWORDS_WEIGHT
            )
            
            numerator = f * (k1 + 1)
            denominator = f + k1 * (1 - b + b * (doc_lengths[doc_id] / avg_doc_length))
            bm25_scores[doc_id] += idf * (numerator / denominator)

    # Second pass: Proximity boost calculation
    proximity_start = time.time()
    for doc_id in bm25_scores.keys():
        doc_length = doc_lengths.get(doc_id, avg_doc_length)
        safe_distance = calculate_safe_distance(doc_length)
        
        proximity_boost = 0
        for i, term1 in enumerate(query_terms[:-1]):
            for term2 in query_terms[i+1:]:
                if term1 in term_positions[doc_id] and term2 in term_positions[doc_id]:
                    pos1 = term_positions[doc_id][term1]
                    pos2 = term_positions[doc_id][term2]
                    
                    prox_score = calculate_proximity_score(pos1, pos2, safe_distance)
                    
                    title_positions1 = [p for p in pos1 if p < 100]
                    title_positions2 = [p for p in pos2 if p < 100]
                    
                    if title_positions1 and title_positions2:
                        title_prox = calculate_proximity_score(
                            title_positions1, title_positions2, safe_distance)
                        proximity_boost += title_prox * TITLE_PROXIMITY_BOOST
                    
                    proximity_boost += prox_score * PROXIMITY_BOOST
        
        bm25_scores[doc_id] *= (1 + proximity_boost)
    
    timing_logs.append(f"Proximity calculation: {time.time() - proximity_start:.4f} seconds")
    
    sorted_scores = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
    timing_logs.append(f"Total calculation time: {time.time() - total_start:.4f} seconds")
    
    return sorted_scores, timing_logs

def write_results_to_file(results, query_terms, timing_logs):
    write_start = time.time()
    with open('result.txt', 'w', encoding='utf-8') as f:
        f.write(f"Search Results for: {' '.join(query_terms)}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Timing Information:\n")
        f.write("-" * 80 + "\n")
        for log in timing_logs:
            f.write(f"{log}\n")
        f.write("-" * 80 + "\n\n")
        
        with DocumentIndex() as doc_index:
        
            for doc_id, score in results[:50]:
                doc = doc_index.get_document(doc_id)
                if doc:
                    f.write(f"Doc ID: {doc_id}\n")
                    f.write(f"Score: {score:.4f}\n")
                    f.write(f"Title: {doc['title']}\n")
                    f.write(f"Keywords: {doc['keywords']}\n")
                    f.write(f"Year: {doc['year']}\n")
                    f.write(f"Venue: {doc['venue']}\n")
                    f.write(f"Citations: {doc['n_citation']}\n")
                    f.write(f"Abstract: {doc['abstract']}\n")
                    f.write("-" * 80 + "\n\n")
        
    print(f"Writing results: {time.time() - write_start:.4f} seconds")

# Initialize metadata
metadata = load_document_metadata()
#doc_lengths = metadata["doc_lengths"]
total_doc_length = metadata["total_doc_length"]
forward_index_length = metadata["forward_index_length"]
avg_doc_length = total_doc_length / forward_index_length

if __name__ == "__main__":
    while True:
        user_query = input("\nEnter search query (or 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break
            
        query_start = time.time()
        query_terms = user_query.split()
        print(f"Query preprocessing: {time.time() - query_start:.4f} seconds")
        
        results, timing_logs = calculate_bm25(query_terms)
        
        if results:
            print(f"\nFound {len(results)} results. Writing to result.txt...")
            write_results_to_file(results[:50], query_terms, timing_logs)
            print("\nTiming Summary:")
            for log in timing_logs:
                print(log)
        else:
            print("No results found.")
