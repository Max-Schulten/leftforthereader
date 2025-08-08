from llama_cpp import Llama
import os
import copy
from threading import Lock

MODEL_PATH =  os.getenv("MODEL_PATH", "app/models/Qwen2.5-Math-1.5B-Instruct-Q4_K_M.gguf")
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a math tutor."
    )
}

# Querying method became asynchronous and was breaking without a thread lock on chat_completion()...
_model = None
_model_lock = Lock()

def get_model():
    return MODEL_PATH.split('/')[-1]

def load_model():
    global _model
    if _model is None:
        _model = Llama(
            model_path=MODEL_PATH,
            n_ctx=1024,
            n_threads=4,
            verbose=False
        )
    return _model

def estimate_tokens(messages: list, model: Llama):
    full_context = " ".join(message["content"] for message in messages)
    return len(model.tokenize(full_context.encode("utf-8")))

def query(prompt: str, rag_context: str, model: Llama, temp: float = 0, messages: list | None = None, max_response_tokens = 1024, max_context_tokens: int = 3500) -> dict:
    print("LLM Work has begun...")
    if messages is None:
        messages = [copy.deepcopy(SYSTEM_PROMPT)]
    else:
        messages = messages.copy()

    messages.append({"role": "user", "content": f"{rag_context}\n\nQuestion: {prompt}"})
    print("Checking history length...")

    while estimate_tokens(messages, model) > max_context_tokens and len(messages) > 3:
        messages.pop(1)  # remove user
        messages.pop(1)  # remove assistant

    print("History OK!")
    try:
        print("Chat Completion Beginning...")
        with _model_lock:
            output = model.create_chat_completion(
                messages=messages,
                max_tokens=max_response_tokens,
                temperature=temp
            )
        print("Chat completion done!")
    except Exception as e:
        return {"Error": str(e)}

    response = output["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": response})

    return {
        "response": response,
        "query": prompt,
        "rag": rag_context,
        "messages": messages
    }
