import pandas as pd
import json
from collections import defaultdict

# Path to the preprocessed file and lexicon
input_file = "data/preprocessed_test_100k.csv"
lexicon_file = "lexicon/lexicon.json"
output_file = "data/forward_index.json"

# Load the lexicon from the specified JSON file
with open(lexicon_file, 'r') as json_file:
    lexicon = json.load(json_file)

# Create a set of valid words for faster lookup
valid_words = set(lexicon.keys())

# Load the CSV file
df = pd.read_csv(input_file)

# Replace NaN values in the relevant columns with empty strings
df.fillna({'title':'','abstract':'','keywords':''}, inplace=True)

# Dictionary to store forward index (docId-> {word_id: {frequency,positons}})
forward_index = {}

# Iterate through each row of the dataframe
for _,row in df.iterrows():
    doc_id = row['id']
    # Concatenate list of words from each column: title, abstract, keywords
    words = row['title'].split() + row['abstract'].split() + row['keywords'].split()

    # Dictionary to store word data for the current document
    word_data = defaultdict(lambda: {'frequency': 0, 'positions': []})

    # Iterate through the words and track their word_id, frequency, and positions
    for position, word in enumerate(words):  
        # Skip words not in the loaded lexicon
        if word not in valid_words:
            continue

        # Access word_id from lexicon (the 'id' field)
        word_id_for_term = lexicon[word]["id"]
        
        # Update word data for the current document
        word_data[word_id_for_term]['positions'].append(position)
        word_data[word_id_for_term]['frequency'] += 1

    # Store the data associated with the document id in forward index
    forward_index[doc_id] = dict(word_data)

# Save forward index to a json file
with open(output_file,'w') as json_file:
   json.dump({'forward_index': forward_index},json_file,indent=4)

print(f"Forward index saved to {output_file}")