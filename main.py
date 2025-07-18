import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any

from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI 
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_pinecone import PineconeVectorStore

# Load environment variables from .env file
load_dotenv()

# --- FastAPI App Initialization ---
app = FastAPI(title="Medical Chatbot API")

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

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
    raise 

# --- Embedding Model and LLM Configuration ---
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", temperature=0.2) 

# --- RAG Chain Setup ---
try:
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings, text_key="text")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) 
    print(f"Pinecone vector store initialized with index: {INDEX_NAME}")
except Exception as e:
    print(f"Error initializing PineconeVectorStore: {e}")
    raise 

# --- Define the Prompt Template for the LLM
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are MediBot, a friendly, helpful, and empathetic medical assistant specializing in diabetes. "
     "Your goal is to provide clear, concise, and accurate information to users based *only* on the provided context. "
     "If the context does not contain enough information to answer the question, state that you don't have enough information. "
     "When answering, be as thorough as possible by including all relevant details from the context. "
     "If the answer involves a list or multiple points, present them clearly using **standard Markdown bullet points** or numbered lists. " # <--- ADJUSTMENT HERE
     "Avoid making up information or providing medical advice beyond what is explicitly stated in the context. "
     "Context: {context}"
    ),
    ("user", "{input}")
])

# Create the document chain (combines context with prompt)
document_chain = create_stuff_documents_chain(llm, prompt)

# Create the retrieval chain (retrieves documents and then passes to document chain)
rag_chain = create_retrieval_chain(retriever, document_chain)

# Pydantic Models for Request/Response
class ChatRequest(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """Handles chat questions and provides answers using RAG."""
    try:
        response = rag_chain.invoke({"input": chat_request.question})
        
        answer = response.get("answer", "Sorry, I could not find an answer to your question based on the available information.")
        
        sources = []
        if "context" in response and response["context"]:
            for doc in response["context"]:
                source_info = []
                if doc.metadata.get("source"):
                    source_info.append(os.path.basename(doc.metadata["source"]))
                if doc.metadata.get("page") is not None:
                    source_info.append(f"Page {doc.metadata['page']}")
                
                if source_info:
                    sources.append(", ".join(source_info))
        
        return ChatResponse(answer=answer, sources=list(set(sources)))
    except Exception as e:
        print(f"Error during chat processing: {e}")
        import traceback
  
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")