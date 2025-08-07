import streamlit as st
import requests
import re
import time
import os
import dotenv

dotenv.load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/")
API_KEY = os.getenv("API_KEY")

st.set_page_config(page_title="L4TR", page_icon="📖")

model_name = None
try:
    resp = requests.get(
        API_URL,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    model_name = data['model']
except Exception as e:
    model_name = f"Error Occured! `{e}`"
    

st.title("Left For The Reader")
st.write("A _RAG-ified Mini LLM_ for mathematics")
st.write("Created by [Max Schulten](https://maxschulten.info): Project Repo [here](https://github.com/max-schulten/leftforthereader)")
st.write(f"Model in Use: `{model_name}`")
st.write(f"RAG Data from [ProofWiki](https://proofwiki.org)")

def math_to_inline(math: str) -> str:
    out = re.sub(r"\\\[|\\\]", "$$", math)
    return re.sub(r"\\\(|\\\)", "$", out)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).markdown(msg["content"])
    
if prompt := st.chat_input("Ask me a math question..."):
    responded = False
    st.session_state["messages"].append({"role": "user", "content": math_to_inline(prompt)})
    st.chat_message("user").markdown(prompt)
    
    with st.status("Thinking...") as status:
        start = time.time()
        try:
            resp = requests.post(
                API_URL + "query",
                json={
                    "prompt": prompt,
                    "messages": st.session_state["messages"]
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "⚠️ No response")
        except Exception as e:
            answer = f"⚠️ An error occured, please try again later."
            status.update(label="An error occured: open to see error.", state="error")
            status.write(f"Error: {e}")
            responded = True
        if not responded:
            status.update(label="Done!", state="complete")
        status.write(f"LLM thought for {round(time.time() - start, 3)}s.")
        
    answer = math_to_inline(answer)
    
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    st.chat_message("assistant").markdown(answer)

if st.session_state["messages"] and len(st.session_state["messages"]) > 0:
    if st.button("🗑️ Clear Chat"):
        st.session_state["messages"] = []
        st.rerun()