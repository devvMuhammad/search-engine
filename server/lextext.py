import json
import ijson

with open("server/data/lexicon.json", "r") as f:
    lexicon = json.load(f)


freqs = {}
INVERTED_INDEX_PATH = "server/data/inverted_index.json"
with open(INVERTED_INDEX_PATH, 'r') as f:
                parser = ijson.kvitems(f, '')
                
                for word_id, postings in parser:
                    freqs[word_id] = len(postings)

# rank by frequency
sorted_freqs = sorted(freqs.items(), key=lambda x: x[1], reverse=True)

# get top 50
top_50 = [lexicon[word_id] for word_id, _ in sorted_freqs[:50]]

print(top_50)
              