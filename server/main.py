import pandas as pd 
import numpy as np

# This is a test which file contains the code for cleaning the ENTIRE dataset
# It reads the large CSV file, extracts the relevant columns, and saves the cleaned data to a new CSV file
def process_dataset(file_path, output_csv, nrows=None):
    try:
        # specify the columns to extract
        columns_to_extract = ['id', 'title', 'abstract','venue', 'keywords', 'year', 'n_citation', 'url']
        df = pd.read_csv(file_path, sep='|', usecols=columns_to_extract, nrows=nrows)

        # drop rows with duplicate ids
        df = df.drop_duplicates(subset=['id'])

        df = df[df['abstract'].str.len() > 100]

        # convert empty arrays in 'keywords' to NaN (or another method of handling empty arrays)
        df['keywords'] = df['keywords'].apply(lambda x: np.nan if x == '[]' else x)
        df["url"] = df["url"].apply(lambda x: np.nan if x == '[]' else x)

        df['venue'] = df['venue'].apply(lambda x: np.nan if x == '{}' else x)

        # drop rows with any null values in the specified columns
        df_cleaned = df.dropna()

        # Ensure each document is on a single line
        df_cleaned = df_cleaned.applymap(lambda x: str(x).replace('\r', ' ').replace('\n', ' '))

        # display the first few rows of the cleaned data to verify
        print(df_cleaned.head())
        
        # save the cleaned data to a new CSV file
        df_cleaned.to_csv(output_csv, index=False)

        print(f"Extracted data saved to {output_csv}")
        print(f"Number of rows extracted: {len(df_cleaned)}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Specify paths in a variable
if __name__ == "__main__":
    input_file = "data/dblp-citation-network-v14.csv"  
    output_file = "data/test_100k.csv"     
    process_dataset(input_file, output_file, 250000)
