import chromadb
import pandas as pd

client = chromadb.PersistentClient(path = 'vectordb')

# Get/Create Definitions collections
defs_collection = client.get_or_create_collection(
    name = "defs"
)

# Read in definitions csv
defs_df = pd.read_csv("final_data/proof_wiki_definitions.csv")[['links', 'terms', 'defs']]

# Concatenate the terms and definitions
defs_df['document'] = f"{defs_df['terms']}: {defs_df['defs']}"

# Write to vector database
for row in defs_df.itertuples():
    defs_collection.add(
        ids = [row.index],
        documents = [row.document],
        metadatas = {
            "term": row.terms,
            "def": row.defs,
            "src": row.links 
        }
    )