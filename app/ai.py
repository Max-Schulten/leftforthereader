from llama_cpp import Llama
import os
import copy

MODEL_PATH =  os.getenv("MODEL_PATH", "app/models/Qwen2.5-Math-1.5B-Instruct-Q4_K_M.gguf")

SYSTEM_PROMPT = {"role": "system", "content": (
            "You are a math tutor. Respond in 5 Sentences at most."
            "Never repeat yourself. If the question is not math, say: 'This is beyond my scope'."
            "If you use one of the sources cite the URL."
        )}

def get_model():
    return MODEL_PATH.split('/')[-1]


def load_model():
    return Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=4,
        verbose=False
    )

def estimate_tokens(messages: list, model: Llama):
    full_context = " ".join(message["content"] for message in messages)
    tokens = len(model.tokenize(full_context.encode("utf-8")))
    return tokens
        
    

def query(prompt: str, rag_context: str, model: Llama, temp: float = 0, messages: list | None = None, max_response_tokens = 1024, max_context_tokens: int = 3500) -> dict:
    
    if messages is None:
        messages = [copy.deepcopy(SYSTEM_PROMPT)]
    else:
        messages = messages.copy()
        
    messages.append({"role": "user", "content": f"{rag_context}\n\nQuestion: {prompt}"})

    while estimate_tokens(messages, model) > max_context_tokens and len(messages) > 3:
        messages.pop(1) # Remove User Message
        messages.pop(1) # Remove Assistant message
    
    try:
        output = model.create_chat_completion(
            messages=messages, # type: ignore
            max_tokens=max_response_tokens,
            temperature=temp
        )
    except Exception as e:
        return {"Error": str(e)}
    
    response = output["choices"][0]["message"]["content"]  # type:ignore
    
    messages.append({"role": "assistant", "content": response})
    
    out = {
        "response": response, # type: ignore
        "query": prompt,
        "rag": rag_context,
        "messages": messages
    }
    
    return out
