from llama_cpp import Llama

MODEL_PATH = "models/Qwen2.5-Math-1.5B-Instruct-Q4_K_M.gguf"

SYSTEM_PROMPT = """You are a math tutor who helps students with various types of mathematics problems proofs, and questions.\n\n"""

def load_model():
    return Llama(
        model_path=MODEL_PATH,
        n_threads=4,
        n_ctx=1024,
        n_batch=64,
        verbose=False
    )

def query(prompt: str, model: Llama, temp: float = 0.5) -> dict:
    
    output = model(
        prompt=SYSTEM_PROMPT + prompt,
        max_tokens=2048,
        temperature=temp,
        top_k=1
    )
    
    out = {
        "response": output["choices"][0]["text"],
        "query": prompt
    }
    
    return out

model = load_model()

print(
    query("Prove that, in a metric space $(X, d)$, the open-ball centered at $x \in X$ $B(x, \delta)$ is in fact open.", model = model)
)