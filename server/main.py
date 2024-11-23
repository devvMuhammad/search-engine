import pandas as pd # type: ignore
import numpy as np # type: ignore

# This file contains the code for cleaning the ENTIRE dataset

def process_dataset(file_path, output_csv, nrows=None):
    try:
        # Read the CSV file using pandas, specifying the columns to extract
        columns_to_extract = ['id', 'title', 'abstract','venue', 'keywords', 'year', 'n_citation', 'url', 'authors','doc_type', 'references']
        df = pd.read_csv(file_path, sep='|', usecols=columns_to_extract, nrows=nrows)

        # remove rows with duplicate ids
        df = df.drop_duplicates(subset=['id'])

        # remove rows with abstracts that are empty strings less than 100 characters
        df = df[df['abstract'].str.len() > 100]

        # Convert empty arrays in 'keywords' to NaN (or another method of handling empty arrays)
        df['keywords'] = df['keywords'].apply(lambda x: np.nan if x == '[]' else x)
        df["url"] = df["url"].apply(lambda x: np.nan if x == '[]' else x)

        # Convert empty objects in 'venue' to NaN
        df['venue'] = df['venue'].apply(lambda x: np.nan if x == '{}' else x)

        # Drop rows with any null values in the specified columns
        df_cleaned = df.dropna()

        # Display the first few rows of the cleaned data to verify
        print(df_cleaned.head())  # Display the first few rows for validation
        

        # Save the cleaned data to a new CSV file
        df_cleaned.to_csv(output_csv, index=False)

        print(f"Extracted data saved to {output_csv}")
        print(f"Number of rows extracted: {len(df_cleaned)}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Usage
input_file = "data/dblp-citation-network-v14.csv"  # Path to the large CSV file
output_file = "data/cleaned_data.csv"     # Output file to save the extracted data
process_dataset(input_file, output_file)

