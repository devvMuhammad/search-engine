import json
from collections import defaultdict

# Path to the forward index and lexicon files
forward_index_file = "data/forward_index.json"
inverted_index_file = "data/inverted_index.json"
lexicon_file = "lexicon/lexicon.json"

# Load the forward index and lexicon
with open(forward_index_file, 'r') as f:
    forward_index = json.load(f)

with open(lexicon_file, 'r') as f:
    lexicon = json.load(f)

# Dictionary to store the inverted index
inverted_index = defaultdict(list)  # Use list directly for storing documents

# Build the inverted index
for doc_id, word_data in forward_index.items():
    for word_id, metadata in word_data.items():
        # Add the document's information to the inverted index for the word_id
        inverted_index[word_id].append({
            'doc_id': doc_id,
            'frequency': metadata['frequency'],
            'positions': metadata['positions']
        })

# Save the inverted index to a JSON file
with open(inverted_index_file, 'w') as f:
    json.dump(inverted_index, f, indent=4)

print(f"Inverted index saved to {inverted_index_file}")
