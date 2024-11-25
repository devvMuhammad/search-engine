import pandas as pd
import json
import os  # Import os module to check if the file exists

# This file contains script for building a lexicon out of 100k preprocessed dataset
def build_simple_lexicon(df):
    lexicon = {}
    
    for column in ['title', 'abstract', 'keywords']:  # Use the 'title' and 'abstract' columns
        for token in df[column]:  # Iterate over the rows of the specified columns
            token = str(token)  # Convert the token to a string
            try:
                token_list = token.split(" ")  # Split the string into words by spaces
                for word in token_list:  # Iterate over the words in the token list
                    if word not in lexicon:
                        lexicon[word] = {"frequency": 1, "id":len(lexicon)}  # Add the word to the lexicon with a count of 1
                    else:
                        lexicon[word]["frequency"] += 1
            except Exception as e:
                print(f"Error: {e} Token: {token} | Token type: {type(token)} | Column: {column}")
                
                continue
    return lexicon


# Check if the lexicon.json file exists; if not, it will be created
file_path = 'lexicon/lexicon.json'
try:
    with open(file_path, 'r') as json_file:
        lexicon = json.load(json_file)
except Exception as e:
    print(f"Lexicon file not found! Creating one in {file_path}!")
    df = pd.read_csv('data/preprocessed_test_100k.csv')  # Load the data (adjust nrows as needed)
    lexicon = build_simple_lexicon(df)  # Build the lexicon
    # create the lexicon directory
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # Save the lexicon to a JSON file, it not exists, then create it
    with open(file_path, 'w') as json_file:
        json.dump(lexicon, json_file, indent=4)

# Function to retrieve the ID of a word from the lexicon
def get_word_id(word):
    # Check if the lexicon exists
    if os.path.exists(file_path):        
        # Check if the word exists in the lexicon
        if word in lexicon:
            return f"The ID of '{word}' is {lexicon[word]}"
        else:
            return f"'{word}' does not exist in the lexicon"
    else:
        return "The lexicon file does not exist."

# Example usage of `get_word_id` function
print(get_word_id('hot'))  # If 'example' exists in the lexicon, it will print its ID; if not, it will print that it's not in the lexicon.
