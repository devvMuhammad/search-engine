import json
import os
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from server.entities.barrels import Barrels
from server.entities.lexicon import Lexicon

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

    def preprocess_text(self, text):
        """Clean and tokenize text"""
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        tokens = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
        return tokens

    def update_lexicon(self, word):
        """Add new word to lexicon if it does not exist"""
        with open(self.lexicon_path, 'r+') as f:
            try:
                lexicon = json.load(f)
                if word not in lexicon:
                    new_id = len(lexicon)
                    lexicon[word] = {"frequency": 1, "id": new_id}
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
        """Update appropriate barrel file"""
        try:
            barrel_id = self.barrels.hash_to_barrel(str(term_id))
            barrel_path = f"{self.barrel_dir}/barrel_{barrel_id}.json"
            
            posting = {
                "doc_id": doc_id,
                "frequency": frequencies,
                "positions": positions
            }
            
            if not os.path.exists(barrel_path):
                with open(barrel_path, 'w') as f:
                    json.dump({str(term_id): [posting]}, f, indent=2)
                return True
            
            try:
                with open(barrel_path, 'r+') as f:
                    data = json.load(f)
                    if str(term_id) not in data:
                        data[str(term_id)] = []
                    data[str(term_id)].append(posting)
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
                return True
            except json.JSONDecodeError:
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

    def add_document(self, doc):
        """Process and add new document"""
        try:
            doc_id = doc['doc_id']
            word_freqs = {}
            positions_dict = {}
            
            sections = [
                (doc['title'], 0),
                (doc['abstract'], 1),
                (' '.join(doc['keywords']) if isinstance(doc['keywords'], list) else doc['keywords'], 2)
            ]
            
            for text, section_id in sections:
                tokens = self.preprocess_text(text)
                for pos, word in enumerate(tokens):
                    term_id = self.update_lexicon(word)
                    print("new term", word, term_id)
                    if term_id not in word_freqs:
                        word_freqs[term_id] = [0, 0, 0]
                        positions_dict[term_id] = []
                    
                    word_freqs[term_id][section_id] += 1
                    positions_dict[term_id].append(pos)
            
            self.append_forward_index(doc_id, word_freqs)
            
            for term_id in word_freqs:
                self.update_barrel(term_id, doc_id, word_freqs[term_id], positions_dict[term_id])
            
            self.append_document_index(doc_id, doc.get('score', 0))
            
            # Add to dataset CSV
            with open(self.dataset_path, 'a', encoding='utf-8') as f:
            # Format CSV line with proper escaping
              csv_line = f'{doc_id},"{doc["title"]}","{doc["abstract"]}","{",".join(doc["keywords"])}","{doc["venue"]}",{doc["year"]},{doc["n_citation"]},"{doc.get("url", "")}"\n'
              f.write(csv_line)

            with open(self.metadata_path, 'r+') as f:
                metadata = json.load(f)
                metadata["forward_index_length"] += 1
                metadata["total_doc_length"] += len(doc["title"].split()) + len(doc["abstract"].split())
               
                f.seek(0)
                json.dump(metadata, f)
                f.truncate()

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
        "doc_id": "test_001",
        "title": "Refactoring UML Models",
        "abstract": "Software developers spend most of their time modifying and maintaining existing products.",
        "keywords": ["basic transformation", "whole model", "structural modification"],
        "venue": "The Unified Modeling Language",
        "year": 2001,
        "n_citation": 360,
        "url": "http://dx.doi.org/10.1007/3-540-45441-1_11",
    }

    print("\n=== Testing Add Content functionality ===\n")
    adder = AddContent()
    print("Processing document...")
    success = adder.add_document(test_doc)
    
    if success:
        print("Document added successfully.")
    else:
        print("Failed to add document.")