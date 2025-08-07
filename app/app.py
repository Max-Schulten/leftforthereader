from fastapi import FastAPI
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import chromadb
import utils
import uvicorn
import ai
import os
import dotenv

# Initialize fast api application
app = FastAPI()

dotenv.load_dotenv()

# Get apikeys
keys = os.getenv("API_KEYS", "").split(' ')

# Load llm
model = ai.load_model()

# Initialize the vector database using persistent vectordb
client = chromadb.PersistentClient(path = "app/vectordb")

def_collection = client.get_collection("defs")

thm_collection = client.get_collection("thms")

# Query structure
class Query(BaseModel):
    prompt: str
    temp: float = 0
    messages: list | None = None

@app.get('/')
def read_root():
    return {
        "status": "OK",
        "model": ai.get_model()
    }

# Main endpoint for responding to queries
@app.post('/query')
async def query(query: Query):

    defs = def_collection.query(
        query_texts=[query.prompt],
        n_results=1
    )
    
    thms = thm_collection.query(
        query_texts=[query.prompt],
        n_results=1
    )

    context = utils.create_context_window(thms=thms, defs=defs)
    
    params = {
        "prompt": query.prompt,
        "rag_context": context,
        "model": model,
        "messages": query.messages
    }

    response = ai.query(**params)
    
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
