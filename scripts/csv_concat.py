import pandas as pd
import os
import re

def concat_csv(dir, pattern = ".*"):
    try:
        file_names = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and bool(re.search(pattern, f))]
    except FileNotFoundError:
        return None
    except NotADirectoryError:
        return None
    
    
    dfs = []
    for filename in file_names:
        path = dir + f"/{filename}"
        df = pd.read_csv(path)
        dfs.append(df)
        
    final_df = pd.concat(dfs)

    try:
        final_df.to_csv("../test.csv")
        return True
    except:
        print("something went wrong!")
        return False
        

concat_csv("./data/proof_wiki_definitions", pattern = ".*.csv$")