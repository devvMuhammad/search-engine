import pandas as pd
import json

# Pre-processed file will be used for forward indexing
input_file = "data/preprocessed_test_100k.csv"

# Load the CSV file
df = pd.read_csv(input_file)

# Replace NaN values in the relevant columns with empty strings
df.fillna({'title':'','abstract':'','keywords':''},inplace=True)

# Dictionary to store lexicon (word -> word_id)
lexicon = {}
word_id = 0 # Initialize word_id counter

# Dictionary to store forward index (docId-> {word_ids: [list],positions:{word_id:[list]},frequencies:{word_id:[count]}})
forward_index = {}

# Iterate through each row of the dataframe
for _,row in df.iterrows():
    doc_id = row['id']
    # Concatenate list of words from each column: title, abstract, keywords
    words = row['title'].split() + row['abstract'].split() + row['keywords'].split()

    # Dictionary to store word frequencies and positions in the current document
    word_positions = {}
    word_frequencies = {}

    # List to store word_ids for the current document
    word_ids = []

    # Iterate through the words and track their word_id, frequency, and positions
    for position,word in enumerate(words):  
        # if word not in lexicon assign a new word_id
        if word not in lexicon:
            lexicon[word] = word_id
            word_id += 1

        word_id_for_term = lexicon[word]
        word_ids.append(word_id_for_term)

        # Update word frequencies and positions in the document
        if word_id_for_term in word_positions:
           word_positions[word_id_for_term].append(position)
           word_frequencies[word_id_for_term] += 1
        else:
            word_positions[word_id_for_term] = [position]
            word_frequencies[word_id_for_term] = 1

    # Store the data associated with the document id in forward index
    forward_index[doc_id] = {
        "word_ids": word_ids,
        "positions": word_positions,
        "frequencies": word_frequencies
    }

# Save lexicon and forward index to a json file
output_file = "data/forward_index.json"

# Write the lexicon and forward index to the file in JSON format
with open(output_file,'w') as json_file:
   json.dump({'lexicon': lexicon,'forward_index': forward_index},json_file,indent=4)
       # separators=(',', ': '))

print(f"Forward index saved to {output_file}")