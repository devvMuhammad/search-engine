import time
import pandas as pd
import json
from collections import defaultdict
from lexicon import Lexicon

class ForwardIndex:
    def __init__(self):
        self.path = "data/forward_index.json"
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
        # specifying paths for preprocessed data and destination of output files
        input_file = "data/preprocessed_test_100k.csv"

        # load the lexicon
        lexiconObj = Lexicon()
        lexicon = lexiconObj.lexicon

        # load the preprocessed data
        df = pd.read_csv(input_file)

        # in case of null vales in title, abstract and keywords, replace them with empty strings
        df.fillna({'title':'','abstract':'','keywords':''}, inplace=True)

        # dictionary to store forward index
        forward_index = {}

        for _,row in df.iterrows():
            doc_id = row['id']
            # combine tokens from title, abstract, keywords
            words = row['title'].split() + row['abstract'].split() + row['keywords'].split()

            # dictionary to store data for a document
            word_dict = defaultdict(lambda: {'frequency': 0, 'positions': []})

            for position, word in enumerate(words):  
                # in case of no word in lexicon, skip (which is unlikely)
                if word not in lexicon:
                    continue

                # get word_id from lexicon
                word_id = lexiconObj.get_word_id(word)
                
                # add position to the 'positions' field and increment frequency
                word_dict[word_id]['positions'].append(position)
                word_dict[word_id]['frequency'] += 1

            # Store the data associated with the document id in forward index
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