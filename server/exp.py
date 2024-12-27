import os
import ijson
import json
import time
from pathlib import Path

BARREL_SIZE_THRESHOLD = 1.5 * 1024 * 1024  # 2MB
BARREL_DIR = "server/data/test_barrels"
INVERTED_INDEX_PATH = "server/data/inverted_index.json"
LEXICON_PATH = "server/data/lexicon.json"
BARREL_METADATA_PATH = "server/data/barrel_metadata.json"

def ensure_barrel_dir():
    Path(BARREL_DIR).mkdir(parents=True, exist_ok=True)

def get_file_size(filepath):
    return os.path.getsize(filepath)

def create_new_barrel(barrel_num):
    barrel_path = os.path.join(BARREL_DIR, f"barrel_{barrel_num}.json")
    with open(barrel_path, 'w') as f:
        f.write('{\n')  # Start JSON structure
    return barrel_path

def build_barrels():
    ensure_barrel_dir()
    word_locations = {}
    current_barrel = 0
    current_barrel_path = create_new_barrel(current_barrel)
    
    first_entry = True
    current_file = open(current_barrel_path, 'a')

    try:
        with open(INVERTED_INDEX_PATH, 'r') as f:
            parser = ijson.kvitems(f, '')
            
            for word_id, postings in parser:
                # Estimate size of new entry
                new_entry = f'{"," if not first_entry else ""}\n  "{word_id}": {json.dumps(postings)}'
                estimated_new_size = get_file_size(current_barrel_path) + len(new_entry.encode('utf-8'))
                
                # If adding this entry would exceed threshold, create new barrel
                if estimated_new_size >= BARREL_SIZE_THRESHOLD +  500 * 1024:
                    current_file.write('\n}')
                    current_file.close()
                    
                    current_barrel += 1
                    current_barrel_path = create_new_barrel(current_barrel)
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
        
        with open(BARREL_METADATA_PATH, 'w') as f:
            json.dump(word_locations, f, indent=1)
            
    except Exception as e:
        print(f"Error building barrels: {e}")
        if not current_file.closed:
            current_file.close()
            
    return current_barrel + 1
# start = time.time()
# build_barrels()
# end = time.time()
def get_barrel(word_id):
    
        if not word_id:
            print(f"Word '{word}' not found in lexicon.")
            return None

        # Load barrel metadata
        with open(BARREL_METADATA_PATH, 'r') as f:
            barrel_metadata = json.load(f)
        
        print(barrel_metadata[word_id])

        if word_id not in barrel_metadata:
            print(f"Word ID {word_id} not found in barrel metadata.")
            return None

        # Load correct barrel
        print(f"Loading word '{word}' with ID {word_id} from barrel {barrel_metadata[word_id]}")
        barrel_path = os.path.join(BARREL_DIR, f"barrel_{barrel_metadata[word_id]}.json")
        if not os.path.exists(barrel_path):
            print(f"Barrel file not found: {barrel_path}")
            return None

        with open(barrel_path, 'r') as f:
            barrel = json.load(f)
            return barrel.get(word_id)

    

# Test the functionality
if __name__ == "__main__":
    # Build barrels if needed
    start = time.time()
    build_barrels()
    end = time.time()
    print(f"Build time: {end - start}")

    # Test word lookup
    # word = "lisp"
    # start = time.time()
    # postings = load_word_postings(word)
    # end = time.time()

    # if postings:
    #     print(f"Found postings for '{word}': {postings}")
    # print(f"Lookup time: {end - start}")