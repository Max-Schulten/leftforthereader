from fastapi import FastAPI
import keyword_extraction as kwe
from pydantic import BaseModel
import chromadb

# Initialize fast api application
app = FastAPI()

# Initialize the vector database using persistent vectordb
client = chromadb.PersistentClient(path = "vectordb")

# Query structure
class Query(BaseModel):
    prompt: str

# Main endpoint for responding to queries
@app.post('/query')
async def query(prompt: Query):

    # get keywords
    keywords = kwe.extractKeywords(prompt.prompt)
    
    # Embed keywords
    kw_embeds = embedder.embed(keywords)

    return(
        {
            "prompt": prompt.prompt,
            "keywords": keywords
        }
    )