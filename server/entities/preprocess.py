import time
import pandas as pd
from lib.utils import preprocess_text

def preprocess_dataset(file_path, output_path):
    """
    We toke the following preprocessing steps:  
    -> Handling contractions
    -> Tokenization
    -> Normalization
    -> Removing stop words
    -> Stemming
    -> Lemmatization
    """

    start_time = time.time()

    # load csv file
    df = pd.read_csv(file_path)

    # preprocess title and abstract
    for column in ['title', 'abstract']:
        df[column] = df[column].apply(lambda x: preprocess_text(x) if isinstance(x, str) else [])

    # preprocess keywords i.e it is an array of strings, just convert to lowercase
    if 'keywords' in df.columns:
        df['keywords'] = df['keywords'].apply(lambda x: [word.lower() for word in x] if isinstance(x, list) else [])

    # save the preprocessed data to the new file
    df.to_csv(output_path, index=False)
  
    end_time = time.time()
    print(f"{len(df)} rows processed.")
    print(f"Preprocessing completed in {end_time - start_time:.2f} seconds.")
    print(f"Processed file saved to: {output_path}")


input_file = "data/test_100k.csv"  
output_file = "data/preprocessed_test_100k.csv" 
preprocess_dataset(input_file, output_file)
