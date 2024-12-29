import time
import json

barrel_path = "../server/data/barrels/barrel_38.json"
start = time.time()

with open(barrel_path, 'r') as f:
    data = json.load(f)
    print(len(data))

end = time.time()
print("Time taken: ", end - start)