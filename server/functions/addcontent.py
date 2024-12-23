import json
import os
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from server.entities.barrels import Barrels  

class AddContent:
    def __init__(self):
        self.lexicon_path = "server/data/lexicon.json"
        self.forward_index_path = "server/data/forward_index.json"
       # self.inverted_index_path = "server/data/inverted_index.json"
        self.barrel_dir = "server/data/barrels/"
        
        # Create directories/files if not exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize empty files if they don't exist"""
        if not os.path.exists(self.lexicon_path):
            with open(self.lexicon_path, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.forward_index_path):
            with open(self.forward_index_path, 'w') as f:
                json.dump({}, f)
                
        if not os.path.exists(self.inverted_index_path):
            with open(self.inverted_index_path, 'w') as f:
                json.dump({}, f)
                
        if not os.path.exists(self.barrel_dir):
            os.makedirs(self.barrel_dir)

    def preprocess_text(self, text):
        """Clean and tokenize text"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans("", "", string.punctuation))
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
        return tokens

    def update_lexicon(self, word):
        """Add new word to lexicon if it does not exist and maintain the updated format."""
        with open(self.lexicon_path, 'r+') as f:
            try:
                lexicon = json.load(f)
                if word not in lexicon:
                    new_id = len(lexicon)
                    # Append new word in the correct format
                    lexicon[word] = {"frequency": 1, "id": new_id}
                    
                    # Write updated lexicon back to file
                    f.seek(0)
                    json.dump(lexicon, f, indent=4)
                    f.truncate()  # Ensure no leftover data after new content
                    return new_id
                else:
                    # Increment frequency if word already exists
                    lexicon[word]["frequency"] += 1
                    
                    # Write updated lexicon back to file
                    f.seek(0)
                    json.dump(lexicon, f, indent=4)
                    f.truncate()
                    return lexicon[word]["id"]
            except json.JSONDecodeError:
                # Handle empty or invalid file by creating a new lexicon
                f.seek(0)
                lexicon = {
                    word: {"frequency": 1, "id": 0}
                }
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

    # def append_inverted_index(self, term_id, doc_id,frequencies,  positions):
    #     """Append posting to inverted index"""
    #     posting = {
    #     "doc_id": doc_id,
    #     "frequency": frequencies,
    #     "positions": positions
    #     }
    #     with open(self.inverted_index_path, 'r+') as f:
    #         f.seek(0, 2)
    #         pos = f.tell()
           
    #         if pos <= 2:
    #             f.seek(0)
    #             f.write('{' + json.dumps({str(term_id): [posting]})[1:-1] + '}')
    #         else:
    #             f.seek(pos - 1)
    #             f.write(',' + json.dumps({str(term_id): [posting]})[1:-1] + '}')

    def update_barrel(self, term_id, doc_id, frequencies, positions):
        """Update appropriate barrel file"""
        
        barrels = Barrels()
        barrel_id = barrels.hash_to_barrel(str(term_id))
        print(f"barell id FOR THE NAYA DOCUMENT IS: {barrel_id}")
        barrel_path = f"{self.barrel_dir}/barrel_{barrel_id}.json"
        
        posting = {
            "doc_id": doc_id,
            "frequency": frequencies,
            "positions": positions
        }
        
        if not os.path.exists(barrel_path):
            with open(barrel_path, 'w') as f:
                json.dump({str(term_id): [posting]}, f, indent=2)
            return
        
        with open(barrel_path, 'r+') as f:
            f.seek(0, 2)  # Go to end
            pos = f.tell()
            
            if pos <= 2:  # Empty file
                f.seek(0)
                f.write('{' + json.dumps({str(term_id): [posting]})[1:-1] + '}')
            else:
                f.seek(pos - 1)  # Move before closing brace
                f.write(',' + json.dumps({str(term_id): [posting]})[1:-1] + '}')
    
    def append_document_index(self, doc_id, score):
        """Append document entry to document index"""
        doc_index_path = "server/data/document_index.json"
        
        # Create file if not exists
        if not os.path.exists(doc_index_path):
            with open(doc_index_path, 'w') as f:
                json.dump({}, f)
        
        with open(doc_index_path, 'r+') as f:
            f.seek(0, 2)  # Go to end
            pos = f.tell()
            
            if pos <= 2:  # Empty file
                f.seek(0)
                f.write('{' + json.dumps({doc_id: score})[1:-1] + '}')
            else:
                f.seek(pos - 1)  # Move before closing brace
                f.write(',' + json.dumps({doc_id: score})[1:-1] + '}')

    def add_document(self, doc):
        """Process and add new document"""
        doc_id = doc['doc_id']
        word_freqs = {}
        positions_dict = {}  # Track positions for each term
        
        # 1. Process sections and update lexicon first
        sections = [
            (doc['title'], 0),
            (doc['abstract'], 1),
            (' '.join(doc['keywords']), 2)
        ]
        
        for text, section_id in sections:
            tokens = self.preprocess_text(text)
            for pos, word in enumerate(tokens):
                # Update lexicon and get term_id
                term_id = self.update_lexicon(word)
                
                # Build frequency and position data
                if term_id not in word_freqs:
                    word_freqs[term_id] = [0, 0, 0]
                    positions_dict[term_id] = []
                
                word_freqs[term_id][section_id] += 1
                positions_dict[term_id].append(pos)
        
        # 2. Update forward index with accumulated frequencies
        self.append_forward_index(doc_id, word_freqs)
        
        # # 3. Update inverted index for each term
        # for term_id in word_freqs:
        #     self.append_inverted_index(term_id, doc_id, 
        #                              word_freqs[term_id],
        #                              positions_dict[term_id])
            
            # 4. Update barrel for each term
        self.update_barrel(term_id, doc_id,
                              word_freqs[term_id],
                              positions_dict[term_id])
        
        # 5. Update document index
        self.append_document_index(doc_id, doc.get('score', 0))
        
        return True

    def add_documents(self, documents):
        """Add multiple documents"""
        for doc in documents:
            success = self.add_document(doc)
            if success:
                print(f"Added document {doc['id']}")
            else:
                print(f"Failed to add document {doc['id']}")


if __name__ == "__main__":
    # Test document in specified format
    test_doc = {
        "abstract": "Software developers spend most of their time modifying and maintaining existing products. This is because systems, and consequently their design, are in perpetual evolution before they die.",
        "citations": "360",
        "doc_id": "fndjsfnjsngjfdngjfn",
        "keywords": [
            "basic transformation",
            "whole model",
            "structural modification",
            "uml model",
            "certain element"
        ],
        "score": 9.317566411530565,
        "title": "Refactoring UML Models",
        "url": ["http://dx.doi.org/10.1007/3-540-45441-1_11"],
        "venue": "{'raw': 'The Unified Modeling Language'}",
        "year": "2001"
    }

    print("\n=== Testing Add Content functionality ===\n")
    
    # Initialize AddContent
    adder = AddContent()
    
    # Process document
    print("Processing document...")
    success = adder.add_document(test_doc)
   
    if success:
        print("Document added successfully.")
    else:
        print("Failed to add document.")