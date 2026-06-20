# tools/rag_tool.py
import os
import pickle
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.tools import tool

# ==========================================
# 1. load and initail Retriever
# ==========================================
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../chroma_db'))
SPLITS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../splits.pkl'))

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


if os.path.exists(DB_PATH) and os.path.exists(SPLITS_PATH):
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    with open(SPLITS_PATH, "rb") as f:
        splits = pickle.load(f)
    bm25_retriever = BM25Retriever.from_documents(splits)
    bm25_retriever.k = 10
    
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever], weights=[0.5, 0.5]
    )
else:
    print("⚠️ If ChromaDB or splits.pkl cannot be found, please check if ingest_data.py has been executed.")
    ensemble_retriever = None

# ==========================================
# 2. A tool that encapsulates Retriever into an Agent that can be used.
# ==========================================
@tool
def query_nxp_knowledge_base(query: str) -> str:
    """
    Search the NXP i.MX93 official knowledge base, EVK manual, and Yocto guide.
    """
    if not ensemble_retriever:
        return "Error: The NXP knowledge base was not loaded correctly and cannot be queried."
    
    print(f"🔍 [[Knowledge Expert is flipping through the manual] '{query}' ...")
    
    enhanced_query = query
    if "base address" in query.lower() or "start address" in query.lower():
        enhanced_query += " (focus on memory map and system memory layout)"
        print(f"🪄 [System] Detected address lookup and has automatically expanded the search terms:{enhanced_query}")

    # execute retriever
    docs = ensemble_retriever.invoke(query)
    
    # Convert the retrieved document into plain text for LLM reading.
    context_list = []
    for i, doc in enumerate(docs, 1):
        source = os.path.basename(doc.metadata.get('source', 'Unknown'))
        context_list.append(f"--- Document Snippet {i} (Source: {source}) ---\n{doc.page_content}")
        
    if not context_list:
        return "No relevant information was found in the knowledge base. Please try changing your keywords."
        
    return "\n\n".join(context_list)