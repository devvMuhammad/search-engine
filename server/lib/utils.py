import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import re
import nltk
from nltk.tokenize import word_tokenize
from contractions import fix 
from autocorrect import spell 

# Initialize and download NLTK tools
nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

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
