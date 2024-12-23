import json
from collections import defaultdict
import math
import time
from server.entities.lexicon import Lexicon
from server.entities.barrels import Barrels
from server.entities.docindex import DocumentIndex

# BM25 parameters
k1 = 1.5  # Term frequency saturation parameter, as this increases, importance of term frequency increases slowly
b = 0.8  # Length normalization parameter, as this decreases, importance of length decreases

# Add section weights at the top with other parameters
TITLE_WEIGHT = 1.1
KEYWORDS_WEIGHT = 0.25
ABSTRACT_WEIGHT = 0.2

# Path to the forward index and lexicon files
forward_index_file = "server/data/forward_index.json"
inverted_index_file = "server/data/inverted_index.json"
lexicon_file = "server/data/lexicon.json"


start = time.time()
lexicon = Lexicon().lexicon
end = time.time()
print("time for loading lexicon: ", end-start)


def load_document_metadata():
    try:
        with open("server/data/metadata.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        
        doc_lengths = {}
        total_doc_length = 0
        from server.entities.forwardindex import ForwardIndex

        # Load the forward index and lexicon
        start = time.time()
        forward_index = ForwardIndex().data
        forward_index_length = len(forward_index)
        end = time.time()

        print("time for loading forward index: ", end-start)
        for doc_id, word_data in forward_index.items():
            doc_length = sum(metadata["frequency"][0]+metadata["frequency"][1] for metadata in word_data.values())
            doc_lengths[doc_id] = doc_length
            total_doc_length += doc_length
        
        metadata = {
            "doc_lengths": doc_lengths,
            "total_doc_length": total_doc_length,
            "forward_index_length": forward_index_length
        }

        with open("server/data/metadata.json", "w") as f:
            json.dump(metadata, f)
        
        return metadata


# Calculate document statistics
metadata = load_document_metadata()
doc_lengths = metadata["doc_lengths"]
total_doc_length = metadata["total_doc_length"]
forward_index_length = metadata["forward_index_length"]

# Average document length
avg_doc_length = total_doc_length / forward_index_length
end = time.time()
print("time taken for calculating doc length and avg: ", end-start)

barrels = Barrels()
# Function to calculate BM25 for a given query
def calculate_bm25(query_terms):
    timing_logs = []
    total_start = time.time()
    
    timing_logs.append(f"Starting BM25 calculation at: {total_start}")
    N = forward_index_length
    bm25_scores = defaultdict(float)
    
    # Create single Barrels instance
    barrel_start = time.time()
    
    timing_logs.append(f"Barrel initialization: {time.time() - barrel_start:.4f} seconds")

    # Process all terms
    for term in query_terms:
        term_start = time.time()
        
        if term not in lexicon:
            continue
        
        word_id = str(lexicon[term]["id"])
        
        # Get docs containing the term
        barrel_load_start = time.time()
        docs = barrels.load_barrel(term)
        timing_logs.append(f"Loading barrel for '{term}': {time.time() - barrel_load_start:.4f} seconds")
        
        if not docs:
            continue

        # Calculate IDF
        idf_start = time.time()
        df = len(docs)
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
        timing_logs.append(f"IDF calculation for '{term}': {time.time() - idf_start:.4f} seconds")

        # Process documents
        scoring_start = time.time()
        for doc in docs:
            doc_id = doc["doc_id"]
            f = (
                doc["frequency"][0] * TITLE_WEIGHT +
                doc["frequency"][1] * ABSTRACT_WEIGHT +
                doc["frequency"][2] * KEYWORDS_WEIGHT
            )
            doc_length = doc_lengths[doc_id]
            numerator = f * (k1 + 1)
            denominator = f + k1 * (1 - b + b * (doc_length / avg_doc_length))
            bm25_scores[doc_id] += idf * (numerator / denominator)
        timing_logs.append(f"Scoring documents for '{term}': {time.time() - scoring_start:.4f} seconds")
        
        timing_logs.append(f"Total processing time for term '{term}': {time.time() - term_start:.4f} seconds")

    # Sort results
    sort_start = time.time()
    sorted_scores = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
    timing_logs.append(f"Sorting results: {time.time() - sort_start:.4f} seconds")
    
    timing_logs.append(f"Total BM25 calculation time: {time.time() - total_start:.4f} seconds")
    print(timing_logs)
    return sorted_scores, timing_logs

def write_results_to_file(results, query_terms, timing_logs):
    write_start = time.time()
    with open('result.txt', 'w', encoding='utf-8') as f:
        f.write(f"Search Results for: {' '.join(query_terms)}\n")
        f.write("=" * 80 + "\n\n")
        
        # Print timing information
        f.write("Timing Information:\n")
        f.write("-" * 80 + "\n")
        for log in timing_logs:
            f.write(f"{log}\n")
        f.write("-" * 80 + "\n\n")
        
        documentIndex = DocumentIndex()
        
        for doc_id, score in results[:50]:
            doc = documentIndex.get_document(doc_id)
            if doc:
                f.write(f"Doc ID: {doc_id}\n")
                f.write(f"Score: {score:.4f}\n")
                f.write(f"Title: {doc['title']}\n")
                # f.write(f"Authors: {doc['authors']}\n")
                f.write(f"Keywords: {doc['keywords']}\n")
                f.write(f"Year: {doc['year']}\n")
                f.write(f"Venue: {doc['venue']}\n")
                f.write(f"Citations: {doc['n_citation']}\n")
                
                # Truncate abstract for preview
                abstract = doc['abstract']
                f.write(f"Abstract: {abstract}\n")
                
                f.write("-" * 80 + "\n\n")
    
    print(f"Writing results to file: {time.time() - write_start:.4f} seconds")

# Infinite loop for user input
if __name__ == "__main__":
    while True:
        user_query = input("\nEnter your search query (or type 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break
            
        query_start = time.time()
        query_terms = user_query.split()
        print(f"Query preprocessing time: {time.time() - query_start:.4f} seconds")
        
        results, timing_logs = calculate_bm25(query_terms)
        
        if results:
            print(f"\nFound {len(results)} results. Writing to result.txt...")
            write_results_to_file(results[:50], query_terms, timing_logs)
            
            # Print timing summary to console
            print("\nTiming Summary:")
            for log in timing_logs:
                print(log)
        else:
            print("No results found for the query.")
