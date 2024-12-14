import os
import json
import hashlib
from collections import defaultdict
import time
import ijson

class Barrels:
    
    def __init__(self, inverted_index_path, barrels_dir, num_barrels=10):
        from server.entities.lexicon import Lexicon
        self.lexicon = Lexicon()
        self.inverted_index_path = inverted_index_path
        self.barrels_dir = barrels_dir
        self.num_barrels = num_barrels
        self.__ensure_dir()

    def __ensure_dir(self):
        """Ensure the barrels directory exists."""
        if not os.path.exists(self.barrels_dir):
            os.makedirs(self.barrels_dir)

    def hash_to_barrel(self, word_id):
        """Assign a word ID to a barrel based on its hash value."""
        return int(hashlib.md5(word_id.encode()).hexdigest(), 16) % self.num_barrels

    def build(self):
        start = time.time()


        """Partition the inverted index into barrels."""
        from server.entities.invertindex import InvertedIndex
        inverted_index = InvertedIndex().data

        # Initialize barrel data
        barrels = [defaultdict(list) for _ in range(self.num_barrels)]

        # Distribute entries into barrels
        for word_id, postings in inverted_index.items():
            barrel_id = self.hash_to_barrel(word_id)
            barrels[barrel_id][word_id] = postings

        # Save each barrel to a separate JSON file
        for i, barrel in enumerate(barrels):
            barrel_path = os.path.join(self.barrels_dir, f"barrel_{i}.json")
            with open(barrel_path, 'w') as f:
                json.dump(barrel, f, indent=2)

        end = time.time()
        print(f"Barrels created in {self.barrels_dir}")
        print(f"Time taken: {end - start}")


    def build_incrementally(self):

        # open barrel files
        barrel_files = {}
        for i in range(self.num_barrels):
            barrel_path = os.path.join(self.barrels_dir, f"barrel_{i}.json")
            barrel_files[i] = open(barrel_path, 'w')
            # start the json file with { and a new line (this is how json files start)
            barrel_files[i].write('{\n')

        # array of flags which indicate if the first entry has been written to the barrel
        first_entry = [True] * self.num_barrels

        # open using ijson
        with open(self.inverted_index_path, 'r') as f:
            # get the key, value pair
            parser = ijson.kvitems(f, '')

            # incremental parsing
            for word_id, postings in parser:
                barrel_id = self.hash_to_barrel(word_id)

                if not first_entry[barrel_id]:
                    barrel_files[barrel_id].write(',\n')
                else:
                    first_entry[barrel_id] = False

                barrel_files[barrel_id].write(f'  "{word_id}": {json.dumps(postings)}')

        # close all barrel files
        for i in range(self.num_barrels):
            # end the json file with a new line and }
            barrel_files[i].write('\n}')
            barrel_files[i].close()


        def load_barrel(self, query_word):

            word_id = str(self.lexicon.get_word_id(query_word))

            """Load the barrel containing the query word."""
            barrel_id = self.hash_to_barrel(str(word_id))
            print(f"barrel_id for {query_word} with id {word_id} is: {barrel_id}")

            barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_id}.json")
            print(f"file path is {barrel_path}")
            try:
                with open(barrel_path, 'r') as f:
                    barrel = json.load(f)
                return barrel[word_id]
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

# takes a function and calculates the time taken to execute it
def calculate_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Time taken: {end - start}")
        return result
    return wrapper

inverted_index_path = "server/data/inverted_index.json"
barrels_dir = "server/data/barrels"

start = time.time()
barrels = Barrels(inverted_index_path, barrels_dir)
end = time.time()
print(f"Time taken to instantiate barrel object: {end-start}")


calculate_time(barrels.build_incrementally)()