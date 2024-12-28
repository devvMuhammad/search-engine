import json
import os
import pandas as pd
import uuid
from server.entities.barrels import Barrels
from server.lib.utils import preprocess_text

class AddContent:
    def __init__(self):
        self.lexicon_path = "server/data/lexicon.json"
        self.forward_index_path = "server/data/forward_index.json"
        self.barrel_dir = "server/data/barrels/"
        self.dataset_path = "server/data/test_100k.csv"
        self.metadata_path = "server/data/metadata.json"
        
        # Initialize files first
        self._initialize_files()
        
        # Load lexicon and initialize counts
        self.lexicon = self._load_lexicon()
        self.words_count = len(self.lexicon)
        self.barrels = Barrels(self.words_count)

    def _load_lexicon(self):
        """Load lexicon from file"""
        try:
            with open(self.lexicon_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _initialize_files(self):
        """Initialize empty files if they don't exist"""
        if not os.path.exists(self.lexicon_path):
            with open(self.lexicon_path, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.forward_index_path):
            with open(self.forward_index_path, 'w') as f:
                json.dump({}, f)
                
        if not os.path.exists(self.barrel_dir):
            os.makedirs(self.barrel_dir)

    def update_lexicon(self, word):
        """Add new word to lexicon if it does not exist"""
        with open(self.lexicon_path, 'r+') as f:
            try:
                lexicon = json.load(f)
                if word not in lexicon:
                    new_id = len(lexicon)
                    lexicon[word] = {"frequency": 1, "id": new_id}
                    print("term", word, new_id)
                else:
                    lexicon[word]["frequency"] += 1
                    new_id = lexicon[word]["id"]
                
                f.seek(0)
                json.dump(lexicon, f, indent=4)
                f.truncate()
                return new_id
                
            except json.JSONDecodeError:
                lexicon = {word: {"frequency": 1, "id": 0}}
                f.seek(0)
                json.dump(lexicon, f, indent=4)
                f.truncate()
                return 0

    def append_forward_index(self, doc_id, word_freqs):
        """Append document to forward index"""
        with open(self.forward_index_path, 'r+') as f:
            f.seek(0, 2)
            pos = f.tell()
            if pos <= 2:  # Empty or minimal JSON
                f.seek(0)
                f.write('{' + json.dumps({doc_id: word_freqs})[1:-1] + '}')
            else:
                f.seek(pos - 1)
                f.write(',' + json.dumps({doc_id: word_freqs})[1:-1] + '}')

    def update_barrel(self, term_id, doc_id, frequencies, positions):
        """Update barrel using metadata lookup approach"""
        try:
            barrel_metadata_path = os.path.join(self.barrel_dir, 'barrel_metadata.json')
            
            # Load barrel metadata
            if os.path.exists(barrel_metadata_path):
                with open(barrel_metadata_path, 'r') as f:
                    barrel_metadata = json.load(f)
            else:
                barrel_metadata = {}

            # Create posting entry
            posting = {
                "doc_id": doc_id,
                "frequency": frequencies,
                "positions": positions
            }

            # Get barrel ID and update
            barrel_id = self.barrels.hash_to_barrel(str(term_id))
            barrel_path = os.path.join(self.barrel_dir, f"barrel_{barrel_id}.json")

            # Update metadata if term not present
            if str(term_id) not in barrel_metadata:
                barrel_metadata[str(term_id)] = barrel_id
                with open(barrel_metadata_path, 'w') as f:
                    json.dump(barrel_metadata, f, indent=2)

            # Update barrel content
            if os.path.exists(barrel_path):
                with open(barrel_path, 'r+') as f:
                    try:
                        data = json.load(f)
                        if str(term_id) not in data:
                            data[str(term_id)] = []
                        data[str(term_id)].append(posting)
                        f.seek(0)
                        json.dump(data, f, indent=2)
                        f.truncate()
                    except json.JSONDecodeError:
                        data = {str(term_id): [posting]}
                        f.seek(0)
                        json.dump(data, f, indent=2)
                        f.truncate()
            else:
                with open(barrel_path, 'w') as f:
                    json.dump({str(term_id): [posting]}, f, indent=2)

            return True

        except Exception as e:
            print(f"Error updating barrel: {e}")
            return False

    def append_document_index(self, doc_id, score):
        """Append document entry to document index"""
        doc_index_path = "server/data/document_index.json"
        
        if not os.path.exists(doc_index_path):
            with open(doc_index_path, 'w') as f:
                json.dump({}, f)
        
        with open(doc_index_path, 'r+') as f:
            try:
                data = json.load(f)
                data[doc_id] = score
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            except json.JSONDecodeError:
                f.seek(0)
                json.dump({doc_id: score}, f, indent=4)
                f.truncate()

    def _generate_doc_id(self):
        """Generate unique document ID using UUID"""
        return f"doc_{str(uuid.uuid4())}"
    
    def document_exists(self, doc_id):
        """Check if document already exists efficiently"""
        try:
            # Check CSV first using pandas read with specific columns
            df = pd.read_csv(self.dataset_path, usecols=['id'])
            if doc_id in df['id'].values:
                return True
                
            # Check document index without loading full file
            doc_index_path = "server/data/document_index.json"
            if os.path.exists(doc_index_path):
                with open(doc_index_path, 'r') as f:
                    for line in f:
                        if doc_id in line:
                            return True
            return False
            
        except Exception as e:
            print(f"Error checking document existence: {e}")
            return False
 
    def add_document(self, doc):
        """Process and add new document"""
        try:
            # Generate unique doc_id first
            doc_id = self._generate_doc_id()
            print(f"Generated document ID: {doc_id}")
            if self.document_exists(doc_id):
             print(f"Document {doc_id} already exists. Generating new ID...")
             return self.add_document(doc)  # Retry with new ID
            
            word_freqs = {}
            positions_dict = {}
            
            sections = [
                (doc['title'], 0),
                (doc['abstract'], 1),
                (' '.join(doc['keywords']) if isinstance(doc['keywords'], list) else doc['keywords'], 2)
            ]
            
            for text, section_id in sections:
                tokens = preprocess_text(text)
                for pos, word in enumerate(tokens.split()):
                    term_id = self.update_lexicon(word)
                    if term_id not in word_freqs:
                        word_freqs[term_id] = [0, 0, 0]
                        positions_dict[term_id] = []
                    
                    word_freqs[term_id][section_id] += 1
                    positions_dict[term_id].append(pos)
            
            self.append_forward_index(doc_id, word_freqs)

            # Convert document to DataFrame row
            new_row = pd.DataFrame([{
                 'id': doc_id,
        'title': doc["title"],
        'keywords': str(doc["keywords"]),
        'venue': str(doc["venue"]),
        'year': doc["year"],
        'n_citation': doc["n_citation"],
        'url': str(doc["url"]),
        'abstract': doc["abstract"],
        'authors': str(doc["authors"]),
        'doc_type': doc["doc_type"],
        'references': str(doc["references"])
            }])
            
            # Append to CSV without writing headers
            new_row.to_csv(self.dataset_path, mode='a', header=False, index=False)
            
            for term_id in word_freqs:
                self.update_barrel(term_id, doc_id, word_freqs[term_id], positions_dict[term_id])
            
            self.append_document_index(doc_id, doc.get('score', 0))
            
    

            with open(self.metadata_path, 'r+') as f:
                metadata = json.load(f)
                metadata["forward_index_length"] += 1
                metadata["total_doc_length"] += len(doc["title"].split()) + len(doc["abstract"].split())
               
                f.seek(0)
                json.dump(metadata, f)
                f.truncate()
            print("metadata updated")
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
          
            
        

    def add_documents(self, documents):
        """Add multiple documents"""
        for doc in documents:
            success = self.add_document(doc)
            if success:
                print(f"Added document {doc.get('doc_id', 'unknown')}")
            else:
                print(f"Failed to add document {doc.get('doc_id', 'unknown')}")

if __name__ == "__main__":
    test_doc = {
         "title": "Deep Learning for Natural Language Processing",
            "keywords": ["neural networks", "NLP", "machine learning", "transformers"],
            "venue": {"raw": "International Conference on Machine Learning 2023"},
            "year": 2023,
            "n_citation": 45,
            "url": ["https://example.com/deep-learning-nlp"],
            "abstract": "This paper presents a comprehensive survey of deep learning techniques applied to natural language processing tasks.",
            "authors": [
                {
                    "id": "author_002",
                    "name": "Jane Smith",
                    "org": "AI Research Institute"
                },
                {
                    "id": "author_003",
                    "name": "Bob Wilson",
                    "org": "Tech University"
                }
            ],
            "doc_type": "Conference",
            "references": ["ref_002", "ref_003", "ref_004"]
    }

    print("\n=== Testing Add Content functionality ===\n")
    adder = AddContent()
    print("Processing document...")
    success = adder.add_document(test_doc)
    
    if success:
        print("Document added successfully.")
    else:
        print("Failed to add document.")