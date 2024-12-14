import os
import json
import hashlib
from collections import defaultdict

class Barrels:
    def __init__(self, inverted_index_path, barrels_dir, num_barrels=10):
        self.inverted_index_path = inverted_index_path
        self.barrels_dir = barrels_dir
        self.num_barrels = num_barrels
        self.__ensure_dir()

    def __ensure_dir(self):
        """Ensure the barrels directory exists."""
        if not os.path.exists(self.barrels_dir):
            os.makedirs(self.barrels_dir)

    def __hash_to_barrel(self, word_id):
        """Assign a word ID to a barrel based on its hash value."""
        return int(hashlib.md5(word_id.encode()).hexdigest(), 16) % self.num_barrels

    def build(self):
        """Partition the inverted index into barrels."""
        try:
            with open(self.inverted_index_path, 'r') as f:
                inverted_index = json.load(f)
        except Exception as e:
            print(f"Error loading inverted index: {e}")
            return

        # Initialize barrel data
        barrels = [defaultdict(list) for _ in range(self.num_barrels)]

        # Distribute entries into barrels
        for word_id, postings in inverted_index.items():
            barrel_id = self.__hash_to_barrel(word_id)
            barrels[barrel_id][word_id] = postings

        # Save each barrel to a separate JSON file
        for i, barrel in enumerate(barrels):
            barrel_path = os.path.join(self.barrels_dir, f"barrel_{i}.json")
            with open(barrel_path, 'w') as f:
                json.dump(barrel, f, indent=2)

        print(f"Barrels created in {self.barrels_dir}")

    def load_barrel(self, query_word):
        """Load the barrel containing the query word."""
        barrel_id = self.__hash_to_barrel(query_word)
        barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_id}.json")

        try:
            with open(barrel_path, 'r') as f:
                barrel = json.load(f)
            return barrel.get(query_word, [])
        except Exception as e:
            print(f"Error loading barrel {barrel_id}: {e}")
            return []

    def count_words_in_barrels(self):
        """Count the number of words in each barrel."""
        word_counts = {}
        
        for i in range(self.num_barrels):
            barrel_path = os.path.join(self.barrels_dir, f"barrel_{i}.json")
            try:
                with open(barrel_path, 'r') as f:
                    barrel = json.load(f)
                word_counts[f"barrel_{i}"] = len(barrel)
            except Exception as e:
                print(f"Error reading barrel {i}: {e}")
                word_counts[f"barrel_{i}"] = 0
        
        return word_counts

# Usage example
inverted_index_path = "server/data/inverted_index.json"
barrels_dir = "server/data/barrels"
    
    # Create and build barrels
barrels = Barrels(inverted_index_path, barrels_dir)
barrels.build()

    # Load postings for a specific word from its barrel
query_word = "machine"
postings = barrels.load_barrel(query_word)
print(f"Postings for '{query_word}': {postings}")

    # Count words in each barrel
word_counts = barrels.count_words_in_barrels()
for barrel, count in word_counts.items():
        print(f"{barrel}: {count} words")