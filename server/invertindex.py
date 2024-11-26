import json
from collections import defaultdict
import math

# Path to the forward index and lexicon files
forward_index_file = "data/forward_index.json"
inverted_index_file = "data/inverted_index.json"
lexicon_file = "lexicon/lexicon.json"

# BM25 parameters
k1 = 1.5  # Term frequency saturation parameter
b = 0.75  # Length normalization parameter

# Load the forward index and lexicon
with open(forward_index_file, 'r') as f:
    forward_index = json.load(f)

with open(lexicon_file, 'r') as f:
    lexicon = json.load(f)

# Calculate document statistics
doc_lengths = {}
total_doc_length = 0

# Compute document lengths and total document length
for doc_id, word_data in forward_index.items():
    doc_length = sum(metadata["frequency"] for metadata in word_data.values())
    doc_lengths[doc_id] = doc_length
    total_doc_length += doc_length

# Average document length
avg_doc_length = total_doc_length / len(forward_index)

# Build the inverted index
inverted_index = defaultdict(list)  # Changed to store documents directly in the list
for doc_id, word_data in forward_index.items():
    for word_id, metadata in word_data.items():
        # Append document information for each word
        inverted_index[word_id].append({
            "doc_id": doc_id,
            "frequency": metadata["frequency"],
            "positions": metadata["positions"]
        })

# Save the inverted index to a JSON file
with open(inverted_index_file, 'w') as f:
    json.dump(inverted_index, f, indent=4)

print(f"Inverted index saved to {inverted_index_file}")

# Function to calculate BM25 for a given query
def calculate_bm25(query_terms):
    N = len(forward_index)  # Total number of documents
    bm25_scores = defaultdict(float)

    for term in query_terms:
        if term not in lexicon:
            continue
        word_id = lexicon[term]["id"]
        if word_id not in inverted_index:
            continue

        # IDF calculation
        df = len(inverted_index[word_id])  # Number of documents containing the term
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)

        # Compute BM25 for each document containing the term
        for doc in inverted_index[word_id]:
            doc_id = doc["doc_id"]
            f = doc["frequency"]  # Term frequency in document
            doc_length = doc_lengths[doc_id]

            # BM25 score calculation
            numerator = f * (k1 + 1)
            denominator = f + k1 * (1 - b + b * (doc_length / avg_doc_length))
            bm25_scores[doc_id] += idf * (numerator / denominator)

    return sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)

# Example query
query = ["machine", "learning"]
results = calculate_bm25(query)

# Display top results
print("Top documents for query:", query)
for doc_id, score in results[:10]:  # Top 10 results
    print(f"Document ID: {doc_id}, BM25 Score: {score}")
