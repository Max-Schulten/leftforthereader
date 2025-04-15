import pandas as pd
import os
import re

def concat_csv(dir, pattern = ".*"):
    try:
        file_names = [f for f in os.listdir() if os.path.isfile(os.path.join(dir, f)) and bool(re.search(pattern, f))]
    except FileNotFoundError:
        return None
    except NotADirectoryError:
        return None
    
    print(file_names)

concat_csv("./data/proof_wiki_definitions", pattern = ".*.csv$")