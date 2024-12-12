import json
from collections import defaultdict
import os
import math

from invertindex import InvertedIndex


class BarrelIndex:
    def __init__(self, num_barrels=10):
        self.num_barrels = num_barrels  # Number of barrels to split the index into
        self.barrel_folder = os.path.join(os.path.dirname(__file__), "../data", "barrels")  # Folder to store the barrels
        os.makedirs(self.barrel_folder, exist_ok=True)

    def build(self, inverted_index):
        """
        Split the inverted index into barrels and save each barrel as a separate file.
        """
        # Calculate the number of items per barrel
        total_words = len(inverted_index)
        words_per_barrel = math.ceil(total_words / self.num_barrels)
        
        # Split the inverted index into barrels
        barrel = defaultdict(list)
        barrel_index = 0
        word_count = 0
        
        for word_id, doc_data in inverted_index.items():
            if word_count >= words_per_barrel:
                # Save the current barrel and start a new one
                self.save_barrel(barrel, barrel_index)
                barrel.clear()
                barrel_index += 1
                word_count = 0

            # Add the current word to the barrel
            barrel[word_id] = doc_data
            word_count += 1
        
        # Save the last barrel
        if barrel:
            self.save_barrel(barrel, barrel_index)

        print(f"Barrels have been created in '{self.barrel_folder}'.")

    def save_barrel(self, barrel, barrel_index):
        """
        Save a single barrel to a JSON file.
        """
        barrel_file = os.path.join(self.barrel_folder, f"barrel_{barrel_index}.json")
        with open(barrel_file, 'w') as f:
            json.dump(barrel, f, indent=2)

    def load_barrel(self, barrel_index):
        """
        Load a barrel from a JSON file.
        """
        barrel_file = os.path.join(self.barrel_folder, f"barrel_{barrel_index}.json")
        try:
            with open(barrel_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Barrel {barrel_index} not found!")
            return {}

    def query(self, word_id):
        """
        Query for a word across all barrels.
        """
        result = []
        for barrel_index in range(self.num_barrels):
            barrel = self.load_barrel(barrel_index)
            if word_id in barrel:
                result.extend(barrel[word_id])

        return result

# Usage example
inverted_index = InvertedIndex().data  # Assuming you have already created the inverted index
barrel_index = BarrelIndex(num_barrels=5)  # Number of barrels can be adjusted
barrel_index.build(inverted_index)

# Query for a word_id
word_id_to_query = 1  # Example word_id
results = barrel_index.query(word_id_to_query)
print(f"Query results for word_id {word_id_to_query}: {results}")
