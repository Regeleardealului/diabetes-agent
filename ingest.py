import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore # Added this import for clarity, though not directly used in ingest_data_to_pinecone

# Load environment variables from .env file
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
INDEX_NAME = "diabetes-knowledge"

if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
    raise ValueError("PINECONE_API_KEY and PINECONE_ENVIRONMENT must be set in the .env file")

# Initialize Pinecone
try:
    pinecone = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    print(f"Successfully initialized Pinecone client for environment: {PINECONE_ENVIRONMENT}")
except Exception as e:
    print(f"Error initializing Pinecone: {e}")
    exit()

# --- Embedding Model Configuration ---
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# --- Document Loading and Splitting ---
PDF_PATH = "knowledge_source/diabetes_common.pdf" 

def load_and_split_pdf(pdf_path):
    """Loads a PDF document and splits it into manageable chunks."""
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return []
    
    print(f"Loading PDF from: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages from PDF.")

    # Split documents into smaller chunks for better retrieval
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split PDF into {len(chunks)} chunks.")
    return chunks

def create_pinecone_index(index_name, dimension, metric="cosine"):
    """Creates a Pinecone index if it doesn't already exist."""
    existing_indexes = [index_info["name"] for index_info in pinecone.list_indexes()]
    
    if index_name not in existing_indexes:
        print(f"Creating Pinecone index: {index_name}...")
        pinecone.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud='aws', region='us-east-1') 
        )
        print(f"Index '{index_name}' created successfully.")
    else:
        print(f"Index '{index_name}' already exists.")

def ingest_data_to_pinecone(chunks, index_name):
    """Generates embeddings for chunks and uploads them to Pinecone."""
    index = pinecone.Index(index_name)
    
    # Check current vector count before upserting (important for unique IDs)
    index_stats = index.describe_index_stats()
    initial_vector_count = index_stats.total_vector_count
    print(f"Initial vector count in index '{index_name}': {initial_vector_count}")

    batch_size = 32
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [chunk.page_content for chunk in batch] 
        
        # Prepare metadata to include the actual text content of the chunk
        metadatas = []
        for chunk in batch:
            meta = {
                "source": os.path.basename(chunk.metadata.get("source", "unknown")),
                "page": chunk.metadata.get("page", 0),
                "text": chunk.page_content 
            }
            metadatas.append(meta)

        try:
            # Generate embeddings
            print(f"Generating embeddings for batch {i//batch_size + 1}...")
            vector_embeddings = embeddings.embed_documents(texts)
            
            # Prepare vectors for upsert
            vectors_to_upsert = []
            for j, emb in enumerate(vector_embeddings):
                # Ensure unique IDs. Using a combination of initial count and batch/chunk index
                doc_id = f"doc_{initial_vector_count + i + j}" 
                vectors_to_upsert.append({"id": doc_id, "values": emb, "metadata": metadatas[j]})
            
            # Upsert to Pinecone
            print(f"Upserting {len(vectors_to_upsert)} vectors to Pinecone...")
            index.upsert(vectors=vectors_to_upsert)
            
            # Optionally, log the new size after upsert
            current_stats = index.describe_index_stats()
            print(f"Batch {i//batch_size + 1} upserted. Current vector count: {current_stats.total_vector_count}")

        except Exception as e:
            print(f"Error during embedding or upsert for batch {i//batch_size + 1}: {e}")

if __name__ == "__main__":
    EMBEDDING_DIMENSION = 768 

    create_pinecone_index(INDEX_NAME, EMBEDDING_DIMENSION)

    document_chunks = load_and_split_pdf(PDF_PATH)

    if document_chunks:
        ingest_data_to_pinecone(document_chunks, INDEX_NAME)
        print("\nData ingestion complete!")
    else:
        print("No document chunks to ingest. Please check PDF path and content.")