import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
import os
import shutil
import json

def create_database_from_pdf(file_path, chroma_path="chroma"):
    # Load config and set up API key
    with open("../llm.json", "r") as f:
        llm_config = json.load(f)

    GOOGLE_API_KEY = llm_config["api_key"]
    genai.configure(api_key=GOOGLE_API_KEY)

    loader = PyPDFLoader(file_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents from {file_path}.")

    # Split files into chunks using a better approach
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Clear out the database first
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY,
    )

    # Create a new DB from the documents
    db = Chroma(
        persist_directory=chroma_path,
        embedding_function=embedding_model
    )
    db.add_documents(chunks)
    db.persist()
    print(f"Saved {len(chunks)} chunks to {chroma_path}.")


def query_database(api_key: str, chroma_path: str, question: str):
    
    genai.configure(api_key=api_key)
    
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key,
    )

    vectordb = Chroma(
        persist_directory=chroma_path,
        embedding_function=embedding_model
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=api_key,
        temperature=0.7,
        convert_system_message_to_human=True
    )

    docs = vectordb.similarity_search(question, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    prompt = f"""Based on the following context, please answer the question.
    Context: {context}
    
    Question: {question}
    """
    
    response = llm.invoke(prompt)
    answer = f"You: {question}\nChatbot: {response.content}"
    return answer

