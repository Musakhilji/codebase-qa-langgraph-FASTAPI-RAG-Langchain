import os
from unittest import result
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langgraph.graph.message import add_messages
from typing import Annotated
from langchain_core.messages import HumanMessage
from app.vectorsstore import build_retriever

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ---------- Check for API Key ----------
if os.getenv("GROQ_API_KEY") is None:
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env or environment before running the script.")

# Groq LLM initialization
llm = ChatGroq(model="openai/gpt-oss-20b", api_key=os.getenv("GROQ_API_KEY"))


# ---------- State ----------
class state(BaseModel):
    query: str = " "
    git_url: str = " "
    result: str = " "
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    question: str = " "
    repo: str = " "
    catogery: str = " "


def node1(state: state):
    query = state.query
    git_url = state.git_url

    data = build_retriever(git_url)
    result = data.invoke(query)

    content = []
    for res in result:
        content.append(res.page_content)

    repo = " ".join(content)

    prompt = f"""You are a friendly and helpful code assistant.
You explain a GitHub project to the user using the code given below.

User Question:
{query}

Code from the project:
{content}

How to answer:

1. If the question is general or vague (for example "what is this about",
   "explain this", "what does it do"), give a simple overview:
   - What the project does (1-2 lines)
   - Main technologies used
   - Main features / endpoints
   - How it works in short steps

2. If the question is specific (a function, a file, a bug, a feature),
   answer exactly that. Show the related code in a code block.

3. If the code only partly answers the question, share what you found
   and say clearly what is missing. Never refuse when you can still
   say something useful.

4. If the question uses different words than the code (for example
   "login" but the code says "auth"), still find the related part
   and use it.

5. You may use your own programming knowledge to explain things better,
   but never invent files, functions or features that are not in the code.

6. Only if the code has nothing related at all, say:
   "I could not find this in the project code. Try asking about its
   main features, files, or endpoints."

Style rules:
- Write in simple, easy English.
- Use short headings and bullet points.
- Put code inside code blocks.
- Do NOT mention "chunks", "retrieved", or chunk numbers.
- Do NOT write a relevance check.
- Do NOT write a Sources section.
- Keep the answer short and clear. No repeated points.
"""
    llm_response = llm.invoke(prompt)

    
    msg = [HumanMessage(content=prompt), llm_response]

    return {
        "messages": msg,
        "repo": repo,        
    }


def node2(state: state):
    messages = state.messages[-1].content
    print("check it is correct or not about your desire or not")
    print(messages)

    
    while True:
        input_query = input("if it is correct then type yes or if it is not correct then type no: ").strip().lower()
        if input_query == "yes" or input_query == "no":
            break

    if input_query == "yes":
        return {
            "catogery": "correct",
        }

    new_query = input("naya query likho: ")
    return {
        "catogery": "incorrect",
        "query": new_query,
    }


def node3(state: state):
    repo = state.repo
    msg=[]
    exit=["exit", "quit", "q","bye","byee",""]
    while True:
     print("plz enter your desire question enter ")
     question = input("question: ")
     if question.lower() in exit:
         print("exiting the loop...")
         break


     
     prompt = f"Code:\n{repo}\n\nQuestion: {question}"
     llm_response = llm.invoke(prompt)
     print(llm_response.content)

     msg.append(HumanMessage(content=question))
     msg.append(llm_response)

    return {
        "messages": msg,
        "question": question,
     }


def node4_router(state: state):
    catogery = state.catogery
    if catogery == "correct":
        return "node3"
    return "node1"


# ---------- Graph ----------
graph = StateGraph(state)

graph.add_node("node1", node1)
graph.add_node("node2", node2)
graph.add_node("node3", node3)

graph.add_edge(START, "node1")
graph.add_edge("node1", "node2")

graph.add_conditional_edges("node2", node4_router, {"node3": "node3", "node1": "node1"})

graph.add_edge("node3", END)

app = graph.compile()

web_graph = StateGraph(state)

web_graph.add_node("node1", node1)

web_graph.add_edge(START, "node1")
web_graph.add_edge("node1", END)

web_app = web_graph.compile()

# ---------- Run ----------
def run(query, git_url):
    ans = web_app.invoke({
        "query": query,
        "git_url": git_url,
    })

    chat = []
    for m in ans["messages"]:
        role = "human" if m.type == "human" else "agent"
        chat.append({"role": role, "content": m.content})

    return {
        "messages": chat,        
        "repo": ans["repo"],     
    }
     
    
 
