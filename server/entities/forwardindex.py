import time
import pandas as pd
import json
from collections import defaultdict
from server.entities.lexicon import Lexicon


class ForwardIndex:
    def __init__(self):
        self.path = "server/data/forward_index.json"
        self.data = self.__load()
        pass

    def __load(self):
        try:
            with open(self.path) as f:
                forward_index = json.load(f)
            return forward_index
        except:
            print(f"Forward Index not found! Creating one in {self.path}")
            return self.__build()


    def __build(self):
        input_file = "server/data/preprocessed_test_100k.csv"
        lexiconObj = Lexicon()
        lexicon = lexiconObj.lexicon
        df = pd.read_csv(input_file)
        df.fillna({'title':'','abstract':'','keywords':''}, inplace=True)
        forward_index = {}

        for _,row in df.iterrows():
            doc_id = row['id']
            # subdive the words into three sections
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
            
            # set the word_dict to the doc_id
            forward_index[doc_id] = dict(word_dict)

        # Save forward index to a json file
        with open(self.path,'w') as j:
            json.dump(forward_index,j,indent=1)

        print(f"Forward index saved to {self.path}")
        return forward_index


start_time = time.time()
forward_index = ForwardIndex().data
end_time = time.time()
print(f"Forward Index built in {end_time - start_time} seconds")