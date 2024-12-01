import json
from collections import defaultdict
import math
import time
from forwardindex import ForwardIndex
from invertindex import InvertedIndex
from lexicon import Lexicon
from preprocess import preprocess_text

# BM25 parameters
k1 = 1.5  # Term frequency saturation parameter
b = 0.75  # Length normalization parameter

# Path to the forward index and lexicon files
forward_index_file = "../data/forward_index.json"
inverted_index_file = "../data/inverted_index.json"
lexicon_file = "../data/lexicon.json"

# Load the forward index and lexicon
start = time.time()
forward_index = ForwardIndex().data
end = time.time()
print("time for loading forward index: ", end-start)

start = time.time()
lexicon = Lexicon().lexicon
end = time.time()
print("time for loading lexicon: ", end-start)

start = time.time()
inverted_index = InvertedIndex().data   
end = time.time()
print("time for loading inverted index: ", end-start)

# Calculate document statistics
doc_lengths = {}
total_doc_length = 0

# Compute document lengths and total document length
start = time.time()
for doc_id, word_data in forward_index.items():
    doc_length = sum(metadata["frequency"] for metadata in word_data.values())
    doc_lengths[doc_id] = doc_length
    total_doc_length += doc_length

# Average document length
avg_doc_length = total_doc_length / len(forward_index)
end = time.time()
print("time taken for calculating doc length and avg: ", end-start)


# Function to calculate BM25 for a given query
def calculate_bm25(query_terms):
    log = []  # Collect logs
    start_time = time.time()

    # Step 1: Preprocess query terms
    preprocess_start = time.time()
    query_terms = [preprocess_text(term) for term in query_terms]
    preprocess_end = time.time()
    log.append(f"Preprocessing query terms took {preprocess_end - preprocess_start:.4f} seconds")
    
    print("query_terms after preprocessing: ", query_terms)

    N = len(forward_index)  # Total number of documents
    bm25_scores = defaultdict(float)

    # Step 2: Iterate through query terms
    for term in query_terms:
        term_start = time.time()
        if term not in lexicon:
            continue
        
        word_id = lexicon[term]["id"]
        word_id = str(word_id)
        if word_id not in inverted_index:
            continue

        # Step 3: IDF calculation
        idf_start = time.time()
        df = len(inverted_index[word_id])  # Number of documents containing the term
        print("Number of documents containing this term: ", df)
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
        idf_end = time.time()
        log.append(f"IDF calculation for term '{term}' took {idf_end - idf_start:.4f} seconds")

        # Step 4: Compute BM25 scores
        bm25_start = time.time()
        for doc in inverted_index[word_id]:
            doc_id = doc["doc_id"]
            f = doc["frequency"]  # Term frequency in document
            doc_length = doc_lengths[doc_id]

            # BM25 score calculation
            numerator = f * (k1 + 1)
            denominator = f + k1 * (1 - b + b * (doc_length / avg_doc_length))
            bm25_scores[doc_id] += idf * (numerator / denominator)  
        bm25_end = time.time()
        log.append(f"BM25 scoring for term '{term}' took {bm25_end - bm25_start:.4f} seconds")
        term_end = time.time()
        log.append(f"Processing term '{term}' took {term_end - term_start:.4f} seconds")

    # Step 5: Sort results
    sort_start = time.time()
    sorted_scores = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
    sort_end = time.time()
    log.append(f"Sorting results took {sort_end - sort_start:.4f} seconds")

    # Log total time
    total_time = time.time() - start_time
    log.append(f"Total BM25 calculation took {total_time:.4f} seconds")

    return sorted_scores, log

# Infinite loop for user input
while True:
    # Get query input from the user
    user_query = input("\nEnter your search query (or type 'exit' to quit): ")
    if user_query.lower() == "exit":
        print("Exiting the program. Goodbye!")
        break

    # Preprocess and split the query into terms
    query_terms = user_query.split()
    
    # Calculate BM25 scores for the query
    results, logs = calculate_bm25(query_terms)
    
    # Display performance logs
    print("\nPerformance Logs:")
    for entry in logs:
        print(entry)
    
    # Display top results
    print("\nTop documents for query:", query_terms)
    if results:
        for doc_id, score in results[:10]:  # Top 10 results
            print(f"Document ID: {doc_id}, BM25 Score: {score}")
    else:
        print("No results found for the query.")
