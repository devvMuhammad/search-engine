import pandas as pd

# Pre-processed file will be used for forward indexing
input_file="data/preprocessed_test_100k.csv"

# Load the CSV file
df = pd.read_csv(input_file)

# Replace NaN values in the relevant columns with empty strings
df.fillna({'title':'','abstract':'','keywords':''},inplace=True)

# Dictionary to store forward index
forward_index={}

# Iterate through each row of the dataframe
for _,row in df.iterrows():
    # Concatenate list of terms from each column: title, abstract, keywords
    terms=row['title'].split()+row['abstract'].split()+row['keywords'].split()

    # Store terms associated with the document id
    forward_index[row['id']]=terms

# Save forward index to a CSV file
output_file="data/forward_index.csv"

# Create a list of tuples for saving to CSV
tuples=[(id,','.join(terms))for id,terms in forward_index.items()]

# Create a dataframe from the above tuples
df_output=pd.DataFrame(tuples,columns=["doc_id","terms"])

# Save to CSV file
df_output.to_csv(output_file,index=False)

print(f"Forward index saved to {output_file}")