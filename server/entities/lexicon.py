import pandas as pd
import json
import os 
import time

class Lexicon:
    path = 'server/data/lexicon.json'
    def __init__(self, load=True):
        # load the lexicon on constructor call
        if load:
            self.lexicon = self.__load()
        
    # private property to load the lexicon
    def __load(self):
        # check if the path exists
        if os.path.exists(self.path):
            with open(self.path, 'r') as json_file:
                return json.load(json_file)
        # if does not exists, then build the lexicon and return it
        else:
            print(f"Lexicon file not found! Creating one in {self.path}!")
            return self.build()
        
    def get_word_id(self, word):
        if word in self.lexicon:
            return self.lexicon[word]["id"]
        else:
            return None
        
    
    def build(self):
        df = pd.read_csv('server/data/preprocessed_test_100k.csv')
        lexicon = {}
        
        for column in ['title', 'abstract', 'keywords']:  
            for token in df[column]:  
                # convert the token to a string for safety purposes
                token = str(token) 
                try:
                    # derive token list from the string token using space as delimiter
                    token_list = token.split(" ") 
                    for word in token_list: 
                        # check if the word already exists in the lexicon
                        if word not in lexicon:
                            # default frequency is 1
                            lexicon[word] = {"frequency": 1, "id":len(lexicon)} 
                        else:
                            # increment frequency by 1 if it already exists
                            lexicon[word]["frequency"] += 1
                # print the error if occurs at a certain token, specifying the token as well
                except Exception as e:
                    print(f"Error: {e} Token: {token} | Token type: {type(token)} | Column: {column}")
                    
                    continue
        # save the lexicon to the path specified in the class privately
        with open(self.path, 'w') as json_file:
            json.dump(lexicon, json_file, indent=4)

        return lexicon
    def update_lexicon(self,new_doc):
        """
        Update the existing lexicon with a new document.
        :param new_doc: Dictionary containing 'title', 'abstract', and 'keywords'.
        """
        for column in ['title', 'abstract', 'keywords']:
            if column in new_doc:
                # Process the text into tokens
                token_list = str(new_doc[column]).split(" ")
                for word in token_list: 
                    # check if the word already exists in the lexicon
                    if word not in self.lexicon:
                        # default frequency is 1
                        self.lexicon[word] = {"frequency": 1, "id":len(self.lexicon)} 
                    else:
                        # increment frequency by 1 if it already exists
                        self.lexicon[word]["frequency"] += 1
        
    
        # save the lexicon to the path specified in the class privately
        with open(self.path, 'w') as json_file:
            json.dump(self.lexicon, json_file, indent=4)

        print(f"Lexicon updated and saved to {self.path}")

        
if __name__ == "__main__":
    lexicon = Lexicon()
    start = time.time()
    lexicon.build()
    end = time.time()
    print(f"Lexicon built in {end-start:.2f} seconds.")
