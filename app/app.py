from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import utils
import uvicorn

# Initialize fast api application
app = FastAPI()

# Initialize the vector database using persistent vectordb
client = chromadb.PersistentClient(path = "vectordb")

def_collection = client.get_collection("defs")

thm_collection = client.get_collection("thms")

# Query structure
class Query(BaseModel):
    prompt: str

# Main endpoint for responding to queries
@app.post('/query')
async def query(prompt: Query):

    defs = def_collection.query(
        query_texts=[prompt.prompt],
        n_results=2
    )
    
    thms = thm_collection.query(
        query_texts=[prompt.prompt],
        n_results=2
    )

    context = utils.create_context_window(thms=thms, defs=defs)
    
    return(
        {
            "prompt": prompt.prompt,
            "context": context
        }
    )
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
