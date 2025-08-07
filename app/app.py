from fastapi import FastAPI, Security, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery
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
API_KEYS = os.getenv("API_KEYS", "").split(' ')

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# Load llm
model = ai.load_model()

# Initialize the vector database using persistent vectordb
client = chromadb.PersistentClient(path = "app/vectordb")

def_collection = client.get_collection("defs")

thm_collection = client.get_collection("thms")

def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    if api_key_query in API_KEYS:
        return api_key_query
    if api_key_header in API_KEYS:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

# Query structure
class Query(BaseModel):
    prompt: str
    temp: float = 0
    messages: list | None = None


@app.get('/')
def read_root(api_key: str = Security(get_api_key)):
    return {
        "status": "OK",
        "model": ai.get_model()
    }

# Main endpoint for responding to queries
@app.post('/query')
async def query(query: Query, api_key: str = Security(get_api_key)):

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
