from collections import defaultdict
import json
import time
from server.entities.forwardindex import ForwardIndex

class InvertedIndex:
    inverted_index_file = "server/data/inverted_index.json"

    def __init__(self):
        self.data = self.__load()
        pass

    def __load(self):
        try:
            with open(self.inverted_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print("Inverted Index not found or corrupted! Creating one in", self.inverted_index_file)
            return self.__build()

    def __build(self):

        # load the lexicon
        forward_index = ForwardIndex().data

        # Build the inverted index
        inverted_index = defaultdict(list)
        for doc_id, word_data in forward_index.items():
            for word_id, metadata in word_data.items():
                # Append document information for each word
                inverted_index[word_id].append({
                    "doc_id": doc_id,
                    "frequency": metadata["frequency"],
                    "positions": metadata["positions"]
                })

        # Save the inverted index to a JSON file
        with open(self.inverted_index_file, 'w') as f:
            json.dump(inverted_index, f, indent=2)

        print(f"Inverted index saved to {self.inverted_index_file}")
        return inverted_index

    def update_inverted_index(self):
        # Load the current forward index (this includes any updates)
        forward_index = ForwardIndex().data

        # Load the existing inverted index (or create a new one if it doesn't exist)
        inverted_index = self.data

        # Update the inverted index with new data from the forward index
        for doc_id, word_data in forward_index.items():
            for word_id, metadata in word_data.items():
                # Check if the word_id already exists in the inverted index
                if word_id not in inverted_index:
                    inverted_index[word_id] = []
                
                # Append new document information for each word
                inverted_index[word_id].append({
                    "doc_id": doc_id,
                    "frequency": metadata["frequency"],
                    "positions": metadata["positions"]
                })
        # Save the updated inverted index back to the JSON file
        with open(self.inverted_index_file, 'w') as f:
            json.dump(inverted_index, f, indent=2)

        print("Inverted Index updated successfully.")
        
startTime = time.time()
inverted_index = InvertedIndex().data
endTime = time.time()
print("Inverted index built in: ", endTime - startTime)