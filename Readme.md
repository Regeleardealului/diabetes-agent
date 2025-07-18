# MediBot: A Diabetes Knowledge Assistant (RAG Chatbot)

![MediBot Chatbot Interface](/medibot.png)

## 🚀 Project Overview

MediBot is an intelligent, AI-powered chatbot designed to provide accurate and helpful information about diabetes. Leveraging the power of Retrieval Augmented Generation (RAG), it consults a dedicated knowledge base (a PDF document) to answer user queries, ensuring responses are grounded in provided data rather than general internet knowledge.

This project showcases a complete full-stack solution, from data ingestion and vector storage to a responsive FastAPI backend API and a sleek, futuristic web-based Graphical User Interface (GUI).

## ✨ Features

* **RAG Architecture:** Combines the strengths of information retrieval and large language models for precise, context-aware answers.
* **Google Gemini Integration:** Utilizes Google's state-of-the-art Generative AI models for embeddings and language generation.
* **Pinecone Vector Database:** Efficiently stores and retrieves document embeddings for rapid knowledge lookup.
* **FastAPI Backend:** A robust and scalable Python API to handle chat interactions.
* **Professional & Futuristic GUI:** A visually appealing web interface built with HTML, CSS, and JavaScript.
* **Markdown Rendering:** Bot responses are rendered with Markdown for clear, structured information (e.g., lists, bold text).
* **Source Citation:** Automatically cites the source document and page number for retrieved information, enhancing transparency and trust.
* **Typing Indicator:** Provides real-time feedback to the user while the bot is processing a response.

## 🧠 Core Logic: Retrieval Augmented Generation (RAG) Explained

The heart of MediBot lies in its RAG (Retrieval Augmented Generation) architecture. This approach addresses the limitations of traditional Large Language Models (LLMs) by providing them with specific, relevant context before generating a response.

Here's how it works:

1.  **Ingestion (`ingest.py`):**
    * A PDF document containing diabetes knowledge is loaded.
    * This document is split into smaller, manageable "chunks" of text. This is crucial because LLMs have token limits, and smaller chunks allow for more precise retrieval.
    * Each chunk is then converted into a numerical representation called an "embedding" using Google's `text-embedding-004` model. Embeddings capture the semantic meaning of the text.
    * These embeddings, along with their original text content and metadata (like source file and page number), are stored in a Pinecone vector database.

2.  **Retrieval & Generation (`main.py`):**
    * When a user asks a question, that question is also converted into an embedding using the same Google embedding model.
    * This question embedding is then used to query the Pinecone vector database. Pinecone finds the most semantically similar text chunks (i.e., the most relevant information) from the knowledge base.
    * These retrieved relevant chunks are then passed as "context" to the `gemini-2.0-flash` Large Language Model.
    * The LLM, guided by a carefully crafted system prompt, generates an answer *based solely on the provided context*. This prevents hallucinations and ensures factual accuracy according to the knowledge base.
    * The answer, along with the source information (filename and page number) from the retrieved chunks, is then sent back to the user interface.

## 🛠️ Technologies & Tools

### Backend & AI Core:
* **Python 3.12**: The primary programming language.
* **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
* **LangChain**: A framework for developing applications powered by language models. It orchestrates the RAG pipeline.
* **Google Generative AI (Gemini)**:
    * **`models/text-embedding-004`**: Used for generating document and query embeddings (768 dimensions).
    * **`models/gemini-2.0-flash`**: The Large Language Model (LLM) used for generating responses. It's a faster, more cost-effective model suitable for conversational AI.
* **Pinecone**: A cloud-native vector database used for efficient storage and retrieval of high-dimensional vector embeddings. The project uses the `Serverless` spec for simplified deployment.
* **`python-dotenv`**: For managing environment variables securely.
* **`pydantic`**: For data validation and settings management with FastAPI.
* **`uvicorn`**: A lightning-fast ASGI server for running FastAPI applications.

### Frontend (GUI):
* **HTML5**: Structure of the web page.
* **CSS3**: Styling for a professional, futuristic aesthetic.
    * **Bootstrap 4.1.3**: For responsive layout and basic UI components.
    * **Custom CSS (`style.css`)**: Implements the dark, glowing, frosted-glass design.
* **JavaScript**: Dynamic functionality and interactivity.
    * **jQuery 3.3.1**: Simplifies DOM manipulation and AJAX requests.
    * **Marked.js**: Renders Markdown syntax in bot responses.
    * **Font Awesome 5.5.0**: Provides icons (e.g., send button).

### Development & Utilities:
* **`.env` file**: Used to securely store sensitive API keys (e.g., `PINECONE_API_KEY`, `GOOGLE_API_KEY`) and other environment-specific configurations. This keeps credentials out of the codebase, which is crucial for public repositories like GitHub.
* **`requirements.txt`**: Lists all Python dependencies required for the project, making it easy to set up the development environment using `pip install -r requirements.txt`.


## 🛠️ Installation & Setup

Follow these steps to get MediBot up and running on your local machine.

1.  **Clone the Repository**
    Start by cloning the project repository to your local machine:
    ```bash
    git clone YOUR_REPO_URL # Replace YOUR_REPO_URL with the actual GitHub URL
    cd Medibot-Diabetes-Assistant
    ```

2.  **Set Up Virtual Environment**
    It's highly recommended to use a Python virtual environment to manage project dependencies and avoid conflicts with other Python projects.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    Once your virtual environment is active, install all the necessary Python packages listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables (`.env`)**
    Create a new file named `.env` in the root directory of your project (i.e., `project_directory/.env`). This file will store your sensitive API keys and other configuration details securely.
    ```
    PINECONE_API_KEY="YOUR_PINECONE_API_KEY"
    PINECONE_ENVIRONMENT="YOUR_PINECONE_ENVIRONMENT" # e.g., "us-east-1"
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    ```
    * **`PINECONE_API_KEY`**: Obtain this from your Pinecone account dashboard.
    * **`PINECONE_ENVIRONMENT`**: This is your Pinecone project's region (e.g., `us-west-2`, `gcp-starter`). You can find this in your Pinecone dashboard.
    * **`GOOGLE_API_KEY`**: Obtain this from Google AI Studio or Google Cloud Console (ensure you have access to Gemini models and Embedding models).

5. **Prepare Knowledge Source**: Place your files (.csv, .pdf, .txt, etc.) in the `knowledge_source/` directory.
