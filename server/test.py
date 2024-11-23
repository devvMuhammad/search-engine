import csv

def read_first_1000_chars(file_path, output_csv):
    try:
        # Open the large file in read mode
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read the first 1000 characters
            content = file.read(1000)

        # Save the content to a CSV file
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Content"])  # Header
            writer.writerow([content])   # The content

        print(f"First 1000 characters written to {output_csv}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Usage
input_file = "data/dblp-citation-network-v14.csv"
output_file = "output_file.csv"
read_first_1000_chars(input_file, output_file)
