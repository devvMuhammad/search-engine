from collections import defaultdict
import json
import time
from server.entities.forwardindex import ForwardIndex

class InvertedIndex:
    inverted_index_file = "server/data/inverted_index.json"

    def __init__(self, load=True):
        if load:
            self.data = self.__load()

    def __load(self):
        try:
            with open(self.inverted_index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading the file: {e}")
            print("Inverted Index not found or corrupted! Creating one in", self.inverted_index_file)
            return self.build()

    def build(self):
        # Load the forward index
        forward_index = ForwardIndex().data

        # Build the inverted index
        inverted_index = defaultdict(list)
        for doc_id, word_data in forward_index.items():
            doc_length = word_data.get("length", 0)  # Get the document length
            # Iterate over the word data
            for word_id, metadata in word_data.get("word_data", {}).items():  # Access the "word_data" key
                # Append document information for each word
                inverted_index[word_id].append({
                    "doc_id": doc_id,
                    "frequency": metadata["frequency"],
                    "positions": metadata["positions"],
                    "length": doc_length  # Store the document length
                })

        # Save the inverted index to a JSON file
        with open(self.inverted_index_file, 'w') as f:
            json.dump(inverted_index, f, indent=2)

        print(f"Inverted index saved to {self.inverted_index_file}")
        return inverted_index

    def update_inverted_index(self):
        # Ensure the inverted index is loaded
        if not hasattr(self, 'data'):
            self.data = self.__load()

        # Load the current forward index (this includes any updates)
        forward_index = ForwardIndex().data

        # Load the existing inverted index (or create a new one if it doesn't exist)
        inverted_index = self.data

        # Update the inverted index with new data from the forward index
        for doc_id, word_data in forward_index.items():
            doc_length = word_data.get("length", 0)  # Get the document length
            for word_id, metadata in word_data.get("word_data", {}).items():
                # Skip 'length' field as it's not a word entry
                if word_id == "length":
                    continue
                # Check if the word_id already exists in the inverted index
                if word_id not in inverted_index:
                    inverted_index[word_id] = []
                
                # Append new document information for each word
                inverted_index[word_id].append({
                    "doc_id": doc_id,
                    "frequency": metadata["frequency"],
                    "positions": metadata["positions"],
                    "length": doc_length  # Store the document length
                })

        # Save the updated inverted index back to the JSON file
        with open(self.inverted_index_file, 'w') as f:
            json.dump(inverted_index, f, indent=2)

        print("Inverted Index updated successfully.")

if __name__ == "__main__":
    startTime = time.time()
    inverted_index = InvertedIndex().data
    endTime = time.time()
    print("Inverted index built in: ", endTime - startTime)
