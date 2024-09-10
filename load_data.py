import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, SimpleDirectoryReader, load_index_from_storage, Settings, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "BAAI/bge-small-en-v1.5"
Settings.llm = Groq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
Settings.embed_model = resolve_embed_model(f"local:{MODEL_NAME}")

def create_index(directory: str, persist: bool = True) -> VectorStoreIndex:

    if not os.path.exists("./propsely"):
        reader = SimpleDirectoryReader(directory)
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.set_index_id("prop")  
        index.storage_context.persist(persist_dir="./propsely")
        return index

    storage_context = StorageContext.from_defaults(persist_dir="./propsely")
    index = load_index_from_storage(
        storage_context=storage_context, 
        index_id="prop"
    )

    return index

def load_data(directory: str) -> VectorStoreIndex:
    index = create_index(directory, persist=True)    
    return index

def get_query_engine(index: VectorStoreIndex):
    return index.as_query_engine(response_mode="tree_summarize")

if __name__ == "__main__":
    index = load_data("data")
    query_engine = get_query_engine(index)
    response = query_engine.query("What is the meaning of life?")
    print(response)
