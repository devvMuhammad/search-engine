import csv
import json
import time
from typing import Dict, Optional, Tuple, List

class DocumentIndex:
    def __init__(self):
        self.csv_path = "server/data/test_100k.csv"
        self.index_path = "server/data/document_index.json"
        # Load the index once during initialization
        try:
            with open(self.index_path, 'r') as index_file:
                self.index = json.load(index_file)
        except FileNotFoundError:
            self.index = {}
        # Keep the CSV file handle as an instance variable
        self.csv_file = None

    def __enter__(self):
        """Context manager entry - opens the CSV file"""
        start = time.time()
        self.csv_file = open(self.csv_path, 'r', encoding='utf-8')
        end = time.time()

        print("mmaz kelite", end-start)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes the CSV file"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None

    def read_next_record(self, csv_file) -> Tuple[Optional[str], int]:
        """Read next CSV record, returning doc_id and start position."""
        start_pos = csv_file.tell()
        
        chunks = []
        while True:
            chunk = csv_file.readline()
            if not chunk:
                return None, 0
                
            chunks.append(chunk)
            try:
                record = next(csv.reader([''.join(chunks)]))
                return record[0], start_pos
            except csv.Error:
                continue
    
    def build_index(self) -> None:
        with open(self.index_path, 'w') as index_file:
            index_file.write('{\n')
            
            with open(self.csv_path, 'r', encoding='utf-8') as csv_file:
                csv_file.readline()  # Skip header
                first = True
                
                while True:
                    doc_id, pos = self.read_next_record(csv_file)
                    if doc_id is None:
                        break
                        
                    if not first:
                        index_file.write(',\n')
                    else:
                        first = False
                        
                    index_file.write(f'"{doc_id}": {pos}')
                    
            index_file.write('\n}')

    def get_documents(self, doc_ids: List[str]) -> List[Optional[Dict]]:
        """Get multiple documents by their IDs efficiently."""
        if not self.csv_file:
            raise RuntimeError("DocumentIndex must be used as a context manager")

        results = []
        for doc_id in doc_ids:
            if doc_id not in self.index:
                results.append(None)
                continue

            self.csv_file.seek(self.index[doc_id])
            content = []
            
            while True:
                chunk = self.csv_file.readline()
                content.append(chunk)
                try:
                    reader = csv.DictReader([''.join(content)],
                                          fieldnames=['id', 'title', 'keywords', 'venue', 
                                                    'year', 'n_citation', 'url', 'abstract',
                                                    'authors', 'doc_type', 'references'])
                    results.append(next(reader))
                    break
                except csv.Error:
                    continue

        return results

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a single document by ID"""
        if not self.csv_file:
            raise RuntimeError("DocumentIndex must be used as a context manager")

        if doc_id not in self.index:
            return None
            
        self.csv_file.seek(self.index[doc_id])
        content = []
        
        while True:
            chunk = self.csv_file.readline()
            content.append(chunk)
            try:
                reader = csv.DictReader([''.join(content)],
                                      fieldnames=['id', 'title', 'keywords', 'venue', 
                                                'year', 'n_citation', 'url', 'abstract',
                                                'authors', 'doc_type', 'references'])
                return next(reader)
            except csv.Error:
                continue
        
if __name__ == "__main__":
    with DocumentIndex() as documentIndex:
        documentIndex.build_index()
        # doc = documentIndex.get_document('0000a1fd')
        # print(doc)