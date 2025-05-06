from chromadb.utils import embedding_functions
import chromadb
import pandas as pd

client = chromadb.PersistentClient(path = 'vectordb')

try:
    client.delete_collection("defs")
    print("Deleted existing 'defs' collection")
except Exception as e:
    print(f"No existing 'defs' collection to delete: {e}")

try:
    client.delete_collection("thms")
    print("Deleted existing 'thms' collection")
except Exception as e:
    print(f"No existing 'thms' collection to delete: {e}")

# Get/Create Definitions collections
defs_collection = client.get_or_create_collection(
    name = "defs"
)

# Read in definitions csv
defs_df = pd.read_csv("final_data/proof_wiki_definitions.csv")[['links', 'terms', 'defs']]

# Concatenate the terms and definitions
defs_df['document'] = "Term:" + defs_df['terms']+ "\n\n" + "Definition:" + defs_df['defs']

print(defs_df['document'])

print(f'Populating {len(defs_df)} rows in vector database for Definitions')

for start in range(0, len(defs_df), 500):
    end = min(start + 500, len(defs_df))

    print(f'Adding batch from index {start} to {end}')

    batch = defs_df.iloc[start:end]
    
    # Generate string ids (just row numbers)
    ids = [f"{i}" for i in range(start, end)]

    # Construct metadatas dict
    metadatas = batch[['terms', 'links']].to_dict(orient='records')
    
    defs_collection.add(
        ids=ids,
        documents=batch['document'].to_list(),
        metadatas=metadatas
    )

# Create theorems collection
thms_collection = client.get_or_create_collection(
    name='thms',
)

# Read in thms csv
thm_df = pd.read_csv("final_data/proof_wiki_theorems.csv")[['links', 'thms', 'proofs']]

# Concatenate theorem and proof
thm_df['document'] = "Theorem/Result:" + thm_df['thms'] + "\n\nProof:" + thm_df['proofs']

for start in range(0, len(thm_df), 500):
    end = min(start + 500, len(thm_df))

    print(f'Adding batch from index {start} to {end}')

    batch = thm_df.iloc[start:end]
    
    # Generate string ids (just row numbers)
    ids = [f"{i}" for i in range(start, end)]

    # Construct metadatas dict
    metadatas = batch[['thms', 'links']].to_dict(orient='records')
    
    thms_collection.add(
        ids=ids,
        documents=batch['document'].to_list(),
        metadatas=metadatas
    )
