import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.chunks import load

load_dotenv()


def build_retriever(repo_url: str):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env or environment "
            "before building the retriever."
        )
    embedding = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    chunks = load(repo_url)
    if not chunks:
        raise ValueError("No documents were loaded to build the vector store.")

    repo_id = hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:16]
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        ids=[
            hashlib.sha256(
                f"{repo_url}\0{chunk.metadata.get('source', '')}\0{chunk.page_content}".encode(
                    "utf-8"
                )
            ).hexdigest()
            for chunk in chunks
        ],
        collection_name=f"repo_{repo_id}",
        persist_directory=str(Path(__file__).resolve().parent / ".chromadb"),
    )
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6},
    )