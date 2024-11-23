import time
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import re
import nltk
from nltk.tokenize import word_tokenize
from contractions import fix 
from autocorrect import spell 

# This script preprocesses the entire dataset into a 50k document csv file (automatically saved to the data folder)

# Initialize and download NLTK tools
nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

# Define preprocessing functions
def handle_contractions(text):
    return fix(text)  # Expands contractions like "don't" -> "do not"

def remove_special_characters(text):
    if isinstance(text, str):
        return re.sub(r'\W+', ' ', text)  # Remove special characters and keep spaces
    return text

def tokenize_text(text):
    if isinstance(text, str):
        return word_tokenize(text)  # Tokenize text into words
    return []

def normalize_text(text):
    if isinstance(text, str):
        text = text.lower()  # Convert to lowercase
        text = re.sub(r'\W+', ' ', text)  # Remove special characters
        return text.strip()
    return text

def remove_stopwords(tokens):
    return [word for word in tokens if word not in stop_words]  # Filter out stopwords

def correct_spelling(tokens):
    return [spell(word) for word in tokens]  # Correct spelling of each word

def stem_tokens(tokens):
    return [stemmer.stem(word) for word in tokens]  # Apply stemming to tokens

def lemmatize_tokens(tokens):
    return [lemmatizer.lemmatize(word) for word in tokens]  # Apply lemmatization to tokens

def preprocess_text(text):
    # Clean text first
    text = remove_special_characters(text)  # Remove special characters
    text = normalize_text(text)  # Normalize the text (convert to lowercase, remove special characters)
    
    # Tokenize the cleaned text
    tokens = word_tokenize(text)  # Tokenize the cleaned text
    
    # Apply stopword removal, spelling correction, stemming, and lemmatization
    tokens = remove_stopwords(tokens)  # Remove stopwords

    # remove tokens with less than 3 characters
    tokens = [word for word in tokens if len(word) > 2]

    # tokens = correct_spelling(tokens)  # Correct spelling if necessary
    tokens = stem_tokens(tokens)  # Apply stemming
    tokens = lemmatize_tokens(tokens)  # Apply lemmatization
    
    return " ".join(tokens)  # Return the list of tokens

def preprocess_dataset(file_path, output_path):
    """
    Preprocess a large dataset CSV file with the following operations:
    - Tokenization
    - Handling contractions
    - Normalization
    - Removing stop words
    - Stemming
    - Lemmatization

    """

    # Start timer
    start_time = time.time()

    # Load the CSV file
    df = pd.read_csv(file_path)

    # Preprocess textual columns
    for column in ['title', 'abstract']:
        if column in df.columns:
            df[column] = df[column].apply(lambda x: preprocess_text(x) if isinstance(x, str) else [])

    # Process 'keywords' column (assuming it's a list of words)
    if 'keywords' in df.columns:
        df['keywords'] = df['keywords'].apply(lambda x: [word.lower() for word in x] if isinstance(x, list) else [])

    # Save the processed dataset
    df.to_csv(output_path, index=False)
  
    # End timer
    end_time = time.time()
    print(f"{len(df)} rows processed.")
    print(f"Preprocessing completed in {end_time - start_time:.2f} seconds.")
    print(f"Processed file saved to: {output_path}")

if __name__ == "__main__":
    input_file = "data/test_100k.csv"  
    output_file = "data/preprocessed_test_100k.csv" 
    preprocess_dataset(input_file, output_file)
