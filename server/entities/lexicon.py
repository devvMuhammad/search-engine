import pandas as pd
import json
import os 

class Lexicon:
    path = '../data/lexicon.json'
    def __init__(self):
        # load the lexicon on constructor call
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
            df = pd.read_csv('data/preprocessed_test_100k.csv')
            return self.build(df)
        
    def get_word_id(self, word):
        if word in self.lexicon:
            return self.lexicon[word]["id"]
        else:
            return None
        
    
    def build(self, df):
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

        

lexicon = Lexicon()
print(lexicon.get_word_id("machine"))
