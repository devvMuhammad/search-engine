# this script is for regenerating everything
from server.main import process_dataset
from server.lib.constants import DATASET_PATH, TEST_DATA_PATH
from server.entities.lexicon import Lexicon
from server.entities.forwardindex import ForwardIndex
from server.entities.invertindex import InvertedIndex
from server.entities.barrels import Barrels
import time

# Specify paths in a variable

# input_file = "server/data/dblp-citation-network-v14.csv"  
# output_file = "server/data/test_100k.csv"   

# start = time.time()
# process_dataset(DATASET_PATH, TEST_DATA_PATH, 250000)
# end = time.time()
# print(f"data processed i {end-start}")

start = time.time()
lexicon = Lexicon()
lexicon.build()
end = time.time()
print(f"lexicon built in {end-start}")

start = time.time()
forward_index = ForwardIndex(load=False)
forward_index.build()
end = time.time()
print(f"forward index built in {end-start}")

start = time.time()
inverted_index = InvertedIndex(load=False)
inverted_index.build()
end = time.time()
print(f"invert index built in {end-start}")

start = time.time()
barrels = Barrels()
barrels.build()
end = time.time()
print(f"barrels built in {end-start}")


