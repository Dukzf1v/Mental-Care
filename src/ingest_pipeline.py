from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.extractors import SummaryExtractor
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding 
import openai
import streamlit as st
from global_settings import STORAGE_PATH, FILES_PATH, CACHE_FILE
from prompts import CUSTOM_SUMMARY_EXTRACT_TEMPLATE

if "openai" in st.secrets and "OPENAI_API_KEY" in st.secrets.openai:
    openai.api_key = st.secrets.openai.OPENAI_API_KEY
else:
    st.error("OpenAI API key is missing in secrets.toml")
    raise ValueError("OpenAI API key is missing.")

Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.2)

def ingest_documents():
    documents = SimpleDirectoryReader(
        input_files=FILES_PATH,
        filename_as_id=True
    ).load_data()
    
    for doc in documents:
        print(doc.id_)

    try:
        cached_hashes = IngestionCache.from_persist_path(CACHE_FILE)
        print("Cache file found. Running using cache...")
    except Exception as e:
        print(f"No cache file found. Running without cache. Error: {e}")
        cached_hashes = IngestionCache() 

    pipeline = IngestionPipeline(
        transformations=[
            TokenTextSplitter(chunk_size=512, chunk_overlap=20),
            SummaryExtractor(summaries=['self'], prompt_template=CUSTOM_SUMMARY_EXTRACT_TEMPLATE), 
            OpenAIEmbedding()
        ],
        cache=cached_hashes
    )

    nodes = pipeline.run(documents=documents)

    pipeline.cache.persist(CACHE_FILE)

    return nodes
