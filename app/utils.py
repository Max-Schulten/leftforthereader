def create_context_window(thms, defs):
    thm_docs = thms['documents'][0]
    
    def_docs = defs['documents'][0]
    
    output = ""
    
    # Add theorems to string
    output = output + "# Potentially Useful Theorem(s)/Results:\n"
    for i in range(len(thm_docs)):
        output = output + f"{thm_docs[i]}\n## Source: {thms['metadatas'][0][i]['links']}\n"
    
    # Add definitions to string
    output = output + "\n\n\n# Potentially Useful Definitions:\n"
    
    for i in range(len(def_docs)):
        output = output + f"{def_docs[i]}\n## Source: {defs['metadatas'][0][i]['links']}\n"

    return output
