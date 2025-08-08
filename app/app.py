from fastapi import FastAPI, Security, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel
import chromadb
import utils
import uvicorn
import ai
import os
import dotenv
import time
import asyncio
from functools import partial

VECTORDB_PATH = os.getenv("VECTORDB_PATH", "app/vectordb")

# Counter for number of requests handling
n_requests = 0

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
client = chromadb.PersistentClient(path = VECTORDB_PATH)

# Retrieve collections
def_collection = client.get_collection("defs")

thm_collection = client.get_collection("thms")

# Run throwaway queries to ensure embedding model is loaded
print(def_collection.query(
        query_texts=["Addition"],
        n_results=1))

print(thm_collection.query(
        query_texts=["Addition"],
        n_results=1))

# For api key validation
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
    global n_requests
    n_requests += 1
    print(f"+NEW REQUEST: NUMBER OF REQUESTS ON SERVER: {n_requests}")
    print("Received AI Query")
    loop = asyncio.get_event_loop()
    print(f"Loop started: {loop}")
    vector_start = time.time()
    defs = def_collection.query(
        query_texts=[query.prompt],
        n_results=1
    )
    
    thms = thm_collection.query(
        query_texts=[query.prompt],
        n_results=1
    )
    
    print(f"Spent {round(time.time() - vector_start, 3)}s Retrieving Documents")

    context = utils.create_context_window(thms=thms, defs=defs)

    params = {
        "prompt": query.prompt + " In 2 sentences.", # In testing, this quantization will massively overshoot length targets. This really helped with long response times
        "rag_context": context,                      # so this acts as a firm nudge towards shorter responses to help with the scarce resources of a VPS
        "model": model,
        "messages": query.messages
    }

    print(f"Querying LLM...")

    response = await loop.run_in_executor(None, partial(ai.query, **params)) # async execution so I can accept multiple requests
    
    n_requests -= 1
    print(f"-REQUEST FINISHED: NUMBER OF REQUESTS ON SERVER: {n_requests}")
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
