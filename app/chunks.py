import hashlib
from pathlib import Path

from git import Repo
from langchain_community.document_loaders import GitLoader
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter


def load(repo_url: str):
    if not repo_url.strip():
        raise ValueError("Repository URL must not be empty.")

    repo_id = hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:16]
    repo_path = Path(__file__).resolve().parent / "repos" / repo_id
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    if repo_path.exists() and not repo_path.is_dir():
        raise ValueError(f"Repository path is not a directory: {repo_path}")

    if not repo_path.exists():
        repo_path.mkdir(parents=True, exist_ok=True)

    if not (repo_path / ".git").exists():
        if any(repo_path.iterdir()):
            raise ValueError(
                f"Repository path {repo_path} is not empty and is not a valid git repo."
            )
        Repo.clone_from(repo_url, str(repo_path), branch="main")

    loader = GitLoader(
        clone_url=repo_url,
        repo_path=str(repo_path),
        branch="main",
        file_filter=lambda file_path: file_path.endswith(".py"),
    )
    documents = loader.load() or []

    if not documents:
        print("No documents found in the Git repository.")
        return []

    print(f"Loaded {len(documents)} documents from the Git repository.")

    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=400,
        chunk_overlap=50,
    )
    return text_splitter.split_documents(documents)
