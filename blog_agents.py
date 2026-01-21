from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# LLM Configuration
# -----------------------------
llm = ChatOllama(
    model="qwen2.5:0.5b", # llama3.2:1b
    temperature=0.7,
)

# -----------------------------
# State Definition
# -----------------------------
class BlogState(TypedDict):
    topic: str
    title: str
    outline: str
    content: str
    refined_content: str

# -----------------------------
# Agents
# -----------------------------
def research_agent(state: BlogState) -> BlogState:
    prompt = ChatPromptTemplate.from_template(
        "You are a research assistant. Create a detailed outline for a blog post about: {topic}\n\n"
        "Provide a structured outline with main points and subpoints."
    )
    result = (prompt | llm).invoke({"topic": state["topic"]})
    state["outline"] = result.content
    return state


def title_agent(state: BlogState) -> BlogState:
    prompt = ChatPromptTemplate.from_template(
        "Based on this topic: {topic}\n\n"
        "Create a catchy, SEO-friendly blog post title. Return ONLY the title."
    )
    result = (prompt | llm).invoke({"topic": state["topic"]})
    state["title"] = result.content.strip()
    return state


def writer_agent(state: BlogState) -> BlogState:
    prompt = ChatPromptTemplate.from_template(
        "You are a professional blog writer.\n\n"
        "Topic: {topic}\n"
        "Title: {title}\n"
        "Outline: {outline}\n\n"
        "Write a well-structured blog post with introduction, body, and conclusion. "
        "Minimum 500 words."
    )
    result = (prompt | llm).invoke({
        "topic": state["topic"],
        "title": state["title"],
        "outline": state["outline"]
    })
    state["content"] = result.content
    return state


def editor_agent(state: BlogState) -> BlogState:
    prompt = ChatPromptTemplate.from_template(
        "You are an editor. Improve the following blog post:\n\n"
        "Title: {title}\n\n"
        "{content}\n\n"
        "Fix grammar, improve clarity, and enhance readability."
    )
    result = (prompt | llm).invoke({
        "title": state["title"],
        "content": state["content"]
    })
    state["refined_content"] = result.content
    return state

# -----------------------------
# Workflow (FIXED NODE NAMES)
# -----------------------------
def create_blog_workflow():
    workflow = StateGraph(BlogState)

    workflow.add_node("do_research", research_agent)
    workflow.add_node("generate_title", title_agent)
    workflow.add_node("write_blog", writer_agent)
    workflow.add_node("edit_blog", editor_agent)

    workflow.set_entry_point("do_research")
    workflow.add_edge("do_research", "generate_title")
    workflow.add_edge("generate_title", "write_blog")
    workflow.add_edge("write_blog", "edit_blog")
    workflow.add_edge("edit_blog", END)

    return workflow.compile()

# -----------------------------
# Blog Generator
# -----------------------------
def generate_blog(topic: str) -> dict:
    workflow = create_blog_workflow()

    initial_state: BlogState = {
        "topic": topic,
        "title": "",
        "outline": "",
        "content": "",
        "refined_content": ""
    }

    result = workflow.invoke(initial_state)

    return {
        "topic": result["topic"],
        "title": result["title"],
        "content": result["refined_content"]
    }

# # -----------------------------
# # Execution
# # -----------------------------
# response = generate_blog("Future of GenAI")
# print("\nTITLE:\n", response["title"])
# print("\nCONTENT:\n", response["content"])

