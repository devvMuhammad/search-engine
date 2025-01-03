import time
import pandas as pd
import json
from collections import defaultdict
from server.entities.lexicon import Lexicon

class ForwardIndex:
    def __init__(self, load=True):
        self.path = "server/data/forward_index.json"
        if load:
            self.data = self.__load()
        pass

    def __load(self):
        try:
            with open(self.path) as f:
                forward_index = json.load(f)
            return forward_index
        except:
            print(f"Forward Index not found! Creating one in {self.path}")
            return self.build()

    def build(self):
        input_file = "server/data/preprocessed_test_100k.csv"
        lexiconObj = Lexicon()
        lexicon = lexiconObj.lexicon
        df = pd.read_csv(input_file)
        df.fillna({'title': '', 'abstract': '', 'keywords': ''}, inplace=True)
        forward_index = {}

        total_doc_length = 0

        for _, row in df.iterrows():
            doc_id = row['id']
            # computing the total length of the document
            total_length = len(row['title'].split()) + len(row['abstract'].split())

            # subdivide the words into three sections
            sections = [
                (row['title'].split(), 0),
                (row['abstract'].split(), 1),
                (row['keywords'].split(), 2)
            ]
            
            # information for each word
            word_dict = defaultdict(lambda: {'frequency': [0, 0, 0], 'positions': []})

            base_position = 0
            
            for words, section_index in sections:
                # iterate through the words in the section
                for current_position, word in enumerate(words):
                    if word in lexicon:
                        word_id = lexiconObj.get_word_id(word)
                        word_dict[word_id]['positions'].append(current_position + base_position)
                        # increment the frequency of the word in that section
                        word_dict[word_id]['frequency'][section_index] += 1
                # update the base position
                base_position += len(words)
            
            # set the word_dict and total length to the doc_id
            forward_index[doc_id] = {
                "word_data": dict(word_dict),
                "length": total_length
            }

            # Update total_doc_length
            total_doc_length += total_length

        # Save forward index to a json file
        with open(self.path, 'w') as j:
            json.dump(forward_index, j, indent=1)

        # Create and save metadata
        metadata = {
            "total_doc_length": total_doc_length,
            "forward_index_length": len(forward_index)
        }

        with open("server/data/metadata.json", "w") as meta_file:
            json.dump(metadata, meta_file, indent=1)
        
        print(f"Forward index saved to {self.path}")
        print(f"Metadata saved to server/data/metadata.json")
        
        return forward_index

    def append_to_forward_index(self, new_doc):
        """
        Append a new document to the existing forward index.
        :para new_doc: Dictionary containing 'id', 'title', 'abstract', and 'keywords'.
        """
        lexiconObj = Lexicon()
        lexicon = lexiconObj.lexicon
        doc_id = new_doc['id']

        total_length = len(new_doc['title'].split()) + len(new_doc['abstract'].split())

        # Subdivide the words into three sections
        sections = [
            (new_doc['title'].split(), 0),  # Section 0: title
            (new_doc['abstract'].split(), 1),  # Section 1: abstract
            (new_doc['keywords'].split(), 2)   # Section 2: keywords
        ]
        
        word_dict = defaultdict(lambda: {'frequency': [0, 0, 0], 'positions': []})
        base_position = 0

        # Iterate through each section of the document
        for words, section_index in sections:
            for current_position, word in enumerate(words):
                if word in lexicon:
                    word_id = lexiconObj.get_word_id(word)
                    word_dict[word_id]['positions'].append(current_position + base_position)
                    word_dict[word_id]['frequency'][section_index] += 1
            base_position += len(words)

        # Append the new document to the forward index
        self.data[doc_id] = {
            "word_data": dict(word_dict),
            "length": total_length  # Add total length
        }

        # Save the updated forward index back to the file
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=1)

        # Update the metadata as well
        total_doc_length = sum([doc['length'] for doc in self.data.values()])
        metadata = {
            "total_doc_length": total_doc_length,
            "forward_index_length": len(self.data)
        }

        with open("server/data/metadata.json", "w") as meta_file:
            json.dump(metadata, meta_file, indent=1)

        print(f"New document with ID {doc_id} added to the forward index.")
        print(f"Metadata updated in server/data/metadata.json.")

if __name__ == "__main__":
    start_time = time.time()
    forward_index = ForwardIndex()
    forward_index.build()
    end_time = time.time()
    print(f"Forward Index built in {end_time - start_time} seconds")