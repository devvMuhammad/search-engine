import os
import json
import hashlib
import time
import ijson


BARREL_SIZE_THRESHOLD = 2 * 1024 * 1024  # Define the threshold size for barrels

class Barrels:
    def __init__(self):
        self.inverted_index_path = "server/data/inverted_index.json"
        self.barrels_dir = "server/data/barrels"
        self.__ensure_dir()
        # self.num_barrels = words_count // 500

    def __ensure_dir(self):
        """Ensure the barrels directory exists."""
        if not os.path.exists(self.barrels_dir):
            os.makedirs(self.barrels_dir)

    def hash_to_barrel(self, word_id):
        """Assign a word ID to a barrel based on its hash value."""
        return int(hashlib.md5(word_id.encode()).hexdigest(), 16) % self.num_barrels

    # def build(self):
    #     """Incrementally partition the inverted index into barrels."""
    #     # Open barrel files
    #     barrel_files = {}
    #     for i in range(self.num_barrels):
    #         barrel_path = os.path.join(self.barrels_dir, f"barrel_{i}.json")
    #         barrel_files[i] = open(barrel_path, 'w')
    #         barrel_files[i].write('{\n')  # Start the JSON file

    #     # Array of flags to track the first entry for each barrel
    #     first_entry = [True] * self.num_barrels

    #     # Incremental parsing using ijson
    #     with open(self.inverted_index_path, 'r') as f:
    #         parser = ijson.kvitems(f, '')

    #         for word_id, postings in parser:
    #             barrel_id = self.hash_to_barrel(word_id)

    #             if not first_entry[barrel_id]:
    #                 barrel_files[barrel_id].write(',\n')
    #             else:
    #                 first_entry[barrel_id] = False

    #             barrel_files[barrel_id].write(f'  "{word_id}": {json.dumps(postings)}')

    #     # Close all barrel files
    #     for i in range(self.num_barrels):
    #         barrel_files[i].write('\n}')
    #         barrel_files[i].close()

    def get_file_size(self, file_path):
        """Get the size of a file in bytes."""
        return os.path.getsize(file_path)

    
    def create_new_barrel(self, barrel_num):
        barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_num}.json")
        with open(barrel_path, 'w') as f:
            f.write('{\n')  # Start JSON structure
        return barrel_path


    def build_barrels(self):
        self.__ensure_dir()
        word_locations = {}
        current_barrel = 0
        current_barrel_path = self.create_new_barrel(current_barrel)
        
        first_entry = True
        current_file = open(current_barrel_path, 'a')

        try:
            with open(self.inverted_index_path, 'r') as f:
                parser = ijson.kvitems(f, '')
                for word_id, postings in parser:
                    # Estimate size of new entry
                    new_entry = f'{"," if not first_entry else ""}\n  "{word_id}": {json.dumps(postings)}'
                    estimated_new_size = self.get_file_size(current_barrel_path) + len(new_entry.encode('utf-8'))
                    
                    # If adding this entry would exceed threshold, create new barrel
                    if estimated_new_size >= BARREL_SIZE_THRESHOLD +  500 * 1024:
                        current_file.write('\n}')
                        current_file.close()
                        
                        current_barrel += 1
                        current_barrel_path = self.create_new_barrel(current_barrel)
                        current_file = open(current_barrel_path, 'a')
                        first_entry = True
                    
                    # Track word location
                    word_locations[word_id] = current_barrel
                    
                    # Write entry
                    if not first_entry:
                        current_file.write(',\n')
                    else:
                        first_entry = False
                    
                    current_file.write(f'  "{word_id}": {json.dumps(postings)}')

            # Close final barrel
            current_file.write('\n}')
            current_file.close()
            
            BARREL_METADATA_PATH = os.path.join('server/data/barrel_metadata.json')
            with open(BARREL_METADATA_PATH, 'w') as f:
                json.dump(word_locations, f, indent=1)
                
        except Exception as e:
            print(f"Error building barrels: {e}")
            if not current_file.closed:
                current_file.close()

        # save the last barrel id to the metadata file
        with open("server/data/metadata.json", 'w+') as f:
            try:
                metadaata = json.load(f)
            except json.JSONDecodeError:
                metadaata = {"last_barrel": current_barrel}
            metadaata["last_barrel"] = current_barrel
            f.seek(0)
            json.dump(metadaata, f, indent=1)
            f.truncate()

        return current_barrel + 1
        
    def get_barrel(self, barrel_id):
        with open(f"server/data/barrels/barrel_{str(barrel_id)}.json", 'r') as f:
            return json.load(f)

    def add_word_to_barrel(self, term_id, doc_id, frequency, position, barrel_metadata, metadata):
        # print(f"Adding word {term_id} to barrels")
        # first check if the word is already in the barrels
        if term_id in barrel_metadata:
            barrel_id = barrel_metadata[term_id]
            barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_id}.json")
            print("already in barrels with path", barrel_path)
            with open(barrel_path, 'r+') as f:
                barrel = json.load(f)
                if term_id in barrel:
                    barrel[term_id].append({
                        "doc_id": doc_id,
                        "frequency": frequency,
                        "positions": position
                    })
                else:
                    barrel[term_id] = [{
                        "doc_id": doc_id,
                        "frequency": frequency,
                        "positions": position
                    }]
                f.seek(0)
                json.dump(barrel, f)
                f.truncate()
            return metadata["last_barrel"]
        

        print("not in barrels")
        # if the word is not in the barrels, fetch the last_barrel number from metadata.json
        last_barrel = metadata["last_barrel"]
        print(f"Last barrel: {last_barrel}")
        # before adding the word to the barrel, check if the size of the barrel is less than the threshold
        barrel_path = os.path.join(self.barrels_dir, f"barrel_{last_barrel}.json")
        if os.path.exists(barrel_path):
            print(f"Barrel {last_barrel} exists")
            print(f"Size of barrel {last_barrel}: {self.get_file_size(barrel_path)}", BARREL_SIZE_THRESHOLD)
            if self.get_file_size(barrel_path) < BARREL_SIZE_THRESHOLD:
                print(f"Adding word {term_id} to existing barrel {last_barrel}")
                with open(barrel_path, 'r+') as f:
                    barrel = json.load(f)
                    if term_id in barrel:
                        barrel[term_id].append({
                            "doc_id": doc_id,
                            "frequency": frequency,
                            "positions": position
                        })
                    else:
                        barrel[term_id] = [{
                            "doc_id": doc_id,
                            "frequency": frequency,
                            "positions": position
                        }]
                    f.seek(0)
                    json.dump(barrel, f)
                    f.truncate()
            else:
                print(f"Creating new barrel {last_barrel + 1} for word {term_id}")
                last_barrel += 1
                new_barrel_path = os.path.join(self.barrels_dir, f"barrel_{last_barrel}.json")
                
                with open(new_barrel_path, 'w') as f:
                    json.dump({term_id: [{
                        "doc_id": doc_id,
                        "frequency": frequency,
                        "positions": position
                    }]}, f)
                
                metadata["last_barrel"] = last_barrel
                with open("server/data/metadata.json", 'w') as f:
                        f.seek(0)
                        json.dump(metadata, f, indent=1)
                        f.truncate()

            barrel_metadata[term_id] = last_barrel
            with open("server/data/barrel_metadata.json", 'w') as f:
                    f.seek(0)
                    json.dump(barrel_metadata, f, indent=1)
                    f.truncate()


    
    def load_barrel(self, word_id):
        """Load the barrel containing the query word."""
        
        barrel_id = self.hash_to_barrel(str(word_id))
        # print(f"Loading barrel {barrel_id} for word {query_word} with id {word_id}")
        barrel_path = os.path.join(self.barrels_dir, f"barrel_{barrel_id}.json")
        print(f"Barrel path: {barrel_path}")
        try:
            with open(barrel_path, 'r') as f:
                barrel = json.load(f)
                # print(barrel[str(word_id)])
                return barrel[str(word_id)]
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
    
    calculate_time(barrels.build_barrels)()

    # with open("server/data/barrel_metadata.json", 'r') as f:
    #     barrel_metadata = json.load(f)
    #     # last_barrel = barrel_metadata["last_barrel"]

    # with open("server/data/metadata.json", 'r') as f:
    #     metadata = json.load(f)

    # barrels.add_word_to_barrel("989898989", "test_doc", [69,69,69], [1,2,3,4], barrel_metadata, metadata)

    # metadata["last_barrel"] = new_last_barrel
    # with open("server/data/metadata.json", 'w') as f:
    #     json.dump(metadata, f, indent=1)

    # barrels.load_barrel(lexicon["lisp"])

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
                    json.dump(barrel, f)
        else:
            # If the barrel does not exist, create it
            with open(barrel_path, 'w') as f:
                json.dump({word_id: [{
                    "doc_id": new_doc_id,
                    "frequency": metadata["frequency"],
                    "positions": metadata["positions"]
                }]}, f)
        print(f"Barrels updated for new document {new_doc_id}")
