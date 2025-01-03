import os
import time
import pandas as pd
from server.lib.utils import preprocess_text

def preprocess_dataset(file_path, output_path):
    """
    We toke the following preprocessing steps:  
    -> Handling contractions
    -> Tokenization
    -> Normalization
    -> Removing stop words
    -> Lemmatization
    """

    start_time = time.time()

    # load csv file
    df = pd.read_csv(file_path)

    # preprocess title and abstract
    for column in ['title', 'abstract']:
        df[column] = df[column].apply(lambda x: preprocess_text(x) if isinstance(x, str) else [])

    # preprocess keywords i.e it is an array of strings, concatenate them into a single string
    if 'keywords' in df.columns:
        df['keywords'] = df['keywords'].apply(lambda x: ' '.join([word.lower() for word in eval(x)]) if isinstance(x, str) else '').apply(lambda x: preprocess_text(x) if isinstance(x, str) else [])

    # save the preprocessed data to the new file
    df.to_csv(output_path, index=False)
  
    end_time = time.time()
    print(f"{len(df)} rows processed.")
    print(f"Preprocessing completed in {end_time - start_time:.2f} seconds.")
    print(f"Processed file saved to: {output_path}")

if __name__ == "__main__":
    print("Preprocessing test_100k.csv")
    input_file = "server/data/test_100k.csv"  
    output_file = "server/data/preprocessed_test_100k.csv" 
    preprocess_dataset(input_file, output_file)

def append_new_document(new_doc,output_path):
    """
    Preprocess and append a single new document."""
    start_time=time.time()
    new_doc['title']=preprocess_text(new_doc['title'])
    new_doc['abstract']=preprocess_text(new_doc['abstract'])
    new_doc['keywords']=[word.lower() for word in new_doc.get('keywords',[])]
    
     # If output file does not exist, write with header; else append without header
    if not os.path.exists(output_path):
        pd.DataFrame([new_doc]).to_csv(output_path, mode='w', header=True, index=False)
    else:
    # Append the new document without rewriting column headers
        pd.DataFrame([new_doc]).to_csv(output_path,mode='a',header=False,index=False)
    print(f"New document appended to in {time.time()-start_time:.2f} seconds.")