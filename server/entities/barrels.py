import os
import json
import hashlib
import time
import ijson


class Barrels:
    def __init__(self):
        self.inverted_index_path = "server/data/inverted_index.json"
        self.barrels_dir = "server/data/barrels"
        self.__ensure_dir()
        from server.entities.lexicon import Lexicon
        lexicon = Lexicon()
         
        words_count = len(lexicon.lexicon)
        self.num_barrels = words_count // 1000
        self.lexicon = lexicon

    def __ensure_dir(self):
        """Ensure the barrels directory exists."""
        if not os.path.exists(self.barrels_dir):
            os.makedirs(self.barrels_dir)

    def hash_to_barrel(self, word_id):
        """Assign a word ID to a barrel based on its hash value."""
        return int(hashlib.md5(word_id.encode()).hexdigest(), 16) % self.num_barrels

    def build(self):
        """Incrementally partition the inverted index into barrels."""
        # Open barrel files
        barrel_files = {}
        for i in range(self.num_barrels):
            barrel_path = os.path.join(self.barrels_dir, f"barrel_{i}.json")
            barrel_files[i] = open(barrel_path, 'w')
            barrel_files[i].write('{\n')  # Start the JSON file

        # Array of flags to track the first entry for each barrel
        first_entry = [True] * self.num_barrels

        # Incremental parsing using ijson
        with open(self.inverted_index_path, 'r') as f:
            parser = ijson.kvitems(f, '')

            for word_id, postings in parser:
                barrel_id = self.hash_to_barrel(word_id)

                if not first_entry[barrel_id]:
                    barrel_files[barrel_id].write(',\n')
                else:
                    first_entry[barrel_id] = False

                barrel_files[barrel_id].write(f'  "{word_id}": {json.dumps(postings)}')

        # Close all barrel files
        for i in range(self.num_barrels):
            barrel_files[i].write('\n}')
            barrel_files[i].close()

    def load_barrel(self, query_word):
        """Load the barrel containing the query word."""
        
        word_id = str(self.lexicon.get_word_id(query_word))
        barrel_id = self.hash_to_barrel(str(word_id))
        # print(f"Loading barrel {barrel_id} for word {query_word} with id {word_id}")
        barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_id}.json")
        print(f"Loading barrel {barrel_id} for word {query_word}")
        try:
            with open(barrel_path, 'r') as f:
                barrel = json.load(f)
            return barrel[word_id]
        except Exception as e:
            print(f"Error loading barrel {barrel_id}: {e}")
            return None

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
    


# Timer decorator to calculate execution time
def calculate_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Time taken: {end - start}")
        return result
    return wrapper


# Build barrels incrementally and measure the time taken
if __name__ == "__main__":
   
    barrels = Barrels()

    # # Ensure at least one barrel is created
    # if num_barrels == 0:
    #     num_barrels = 1
    
    # calculate_time(barrels.build)()

    barrels.load_barrel("lisp")

def update_barrels(self, new_doc_id, new_postings):
    """Update barrels when a new document is added to the index."""
        
    # Step 1: Update the barrels by adding the new document's word postings
    for word_id, metadata in new_postings.items():
        barrel_id = self.hash_to_barrel(str(word_id))
        barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_id}.json")

        # Open and update the barrel
        if os.path.exists(barrel_path):
            with open(barrel_path, 'r+') as f:
                barrel = json.load(f)
                if word_id in barrel:
                    barrel[word_id].append({
                         "doc_id": new_doc_id,
                         "frequency": metadata["frequency"],
                         "positions": metadata["positions"]
                        })
                else:
                    barrel[word_id] = [{
                        "doc_id": new_doc_id,
                        "frequency": metadata["frequency"],
                        "positions": metadata["positions"]
                        }]
                
                 # Re-save the updated barrel
                    f.seek(0)
                    json.dump(barrel, f, indent=2)
        else:
            # If the barrel does not exist, create it
            with open(barrel_path, 'w') as f:
                json.dump({word_id: [{
                    "doc_id": new_doc_id,
                    "frequency": metadata["frequency"],
                    "positions": metadata["positions"]
                }]}, f, indent=2)
        print(f"Barrels updated for new document {new_doc_id}")
