# Codebase Q&A Agent

An AI agent that indexes any GitHub repository and answers questions about it, with **file path citations**.

Example:

```
Q: Where is authentication handled?
A: Auth logic lives in `app/auth/jwt.py` (function `verify_token`),
   and it is used by the routes in `app/routes/login.py`.
```

## Features

- Clones a GitHub repo and chunks the code at **file / function level**
- Stores chunks as embeddings in a vector database (RAG)
- LangGraph workflow: retrieve -> answer
- Every answer includes file path citations

## Tech Stack

- Python
- LangGraph + LangChain
- ChromaDB (vector store)
- HuggingFace embeddings
- Groq LLM
- GitPython

## Installation

```bash
# 1. Clone this repo
git clone https://github.com/Musakhilji/codebase-qa-agent.git
cd codebase-qa-agent

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / Mac

# 3. Install dependencies
pip install -r requirements.txt
```

## Setup

Create a `.env` file in the project folder:

```
GROQ_API_KEY=your_api_key_here
```

## Usage

```bash
python main.py
```

Enter a GitHub repo URL, wait for indexing to finish, then start asking questions.

## Project Structure

```
codebase-qa-agent/
├── main.py            # entry point
├── requirements.txt
├── .env               # API keys (do not push to GitHub)
└── README.md
```

## How It Works

1. **Clone**: the repo is downloaded
2. **Chunk**: code is split by file and function
3. **Embed**: chunks are stored in the vector DB
4. **Retrieve**: the most relevant chunks are found for the question
5. **Answer**: the LLM answers and cites file paths

## Author

Musa Khilji - [GitHub](https://github.com/Musakhilji)