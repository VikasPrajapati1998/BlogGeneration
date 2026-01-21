from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# -----------------------------
# LLM Configuration
# -----------------------------
llm = ChatOllama(
    model="qwen2.5:0.5b",
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
    approval_status: str  # "pending", "approved", "rejected"
    rejection_reason: str

# -----------------------------
# Agents (Nodes)
# -----------------------------
def research_agent(state: BlogState) -> BlogState:
    """Research and create outline"""
    print(f"[AGENT] Research Agent: Creating outline for '{state['topic']}'")
    prompt = ChatPromptTemplate.from_template(
        "You are a research assistant. Create a detailed outline for a blog post about: {topic}\n\n"
        "Provide a structured outline with main points and subpoints."
    )
    result = (prompt | llm).invoke({"topic": state["topic"]})
    state["outline"] = result.content
    print(f"[AGENT] Research complete")
    return state


def title_agent(state: BlogState) -> BlogState:
    """Generate blog title"""
    print(f"[AGENT] Title Agent: Generating title")
    prompt = ChatPromptTemplate.from_template(
        "Based on this topic: {topic}\n\n"
        "Create a catchy, SEO-friendly blog post title. Return ONLY the title."
    )
    result = (prompt | llm).invoke({"topic": state["topic"]})
    state["title"] = result.content.strip()
    print(f"[AGENT] Title generated: {state['title']}")
    return state


def writer_agent(state: BlogState) -> BlogState:
    """Write blog content"""
    print(f"[AGENT] Writer Agent: Writing blog")
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
    print(f"[AGENT] Writing complete ({len(state['content'])} chars)")
    return state


def editor_agent(state: BlogState) -> BlogState:
    """Edit and refine content"""
    print(f"[AGENT] Editor Agent: Refining content")
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
    state["approval_status"] = "pending"
    print(f"[AGENT] Editing complete - READY FOR HUMAN REVIEW")
    return state


def human_approval_node(state: BlogState) -> BlogState:
    """
    CHECKPOINT NODE - Execution pauses here
    This node will be interrupted before execution
    Human will update the state externally
    """
    print(f"[CHECKPOINT] Human approval node - this should not execute during initial run")
    print(f"[CHECKPOINT] Current approval status: {state.get('approval_status', 'pending')}")
    print(f"[CHECKPOINT] Blog: '{state.get('title', 'N/A')}'")
    # This node just passes through - the actual update happens via update_state()
    return state


def finalize_approved(state: BlogState) -> BlogState:
    """Final node for approved blogs"""
    print(f"[FINAL] ✓ Blog APPROVED: '{state['title']}'")
    return state


def handle_rejection(state: BlogState) -> BlogState:
    """Handle rejected blogs"""
    reason = state.get('rejection_reason', 'No reason provided')
    print(f"[FINAL] ✗ Blog REJECTED: '{state['title']}'")
    print(f"[FINAL] Rejection reason: {reason}")
    return state


def route_approval(state: BlogState) -> str:
    """
    Router function - decides next step based on approval_status
    """
    approval = state.get("approval_status", "pending")
    print(f"[ROUTER] Checking approval status: {approval}")
    
    if approval == "approved":
        print(f"[ROUTER] → Routing to APPROVED path")
        return "approved"
    elif approval == "rejected":
        print(f"[ROUTER] → Routing to REJECTED path")
        return "rejected"
    else:
        # This shouldn't happen if workflow is properly paused
        print(f"[ROUTER] ⚠️ Unexpected status '{approval}'")
        return "approved"


# -----------------------------
# SQLite Checkpointer Setup
# -----------------------------
def get_checkpointer():
    """Create SQLite checkpointer for persistent state"""
    # Use real SQLite connection with check_same_thread=False for multi-process access
    conn = sqlite3.connect("blog_workflow.db", check_same_thread=False)
    return SqliteSaver(conn)


# -----------------------------
# Workflow Graph Builder
# -----------------------------
def create_blog_workflow():
    """Create the workflow graph with SQLite checkpointing and HITL"""
    print("[WORKFLOW] Creating workflow with SQLite checkpointer...")
    
    # Create SQLite checkpointer
    checkpointer = get_checkpointer()
    
    workflow = StateGraph(BlogState)

    # Add all nodes
    workflow.add_node("do_research", research_agent)
    workflow.add_node("generate_title", title_agent)
    workflow.add_node("write_blog", writer_agent)
    workflow.add_node("edit_blog", editor_agent)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("finalize_approved", finalize_approved)
    workflow.add_node("handle_rejection", handle_rejection)

    # Set up the flow
    workflow.set_entry_point("do_research")
    workflow.add_edge("do_research", "generate_title")
    workflow.add_edge("generate_title", "write_blog")
    workflow.add_edge("write_blog", "edit_blog")
    workflow.add_edge("edit_blog", "human_approval")
    
    # Add conditional edges after human approval
    workflow.add_conditional_edges(
        "human_approval",
        route_approval,
        {
            "approved": "finalize_approved",
            "rejected": "handle_rejection"
        }
    )
    
    # Both paths end the workflow
    workflow.add_edge("finalize_approved", END)
    workflow.add_edge("handle_rejection", END)

    # Compile with checkpointing and interrupt BEFORE human_approval
    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"]
    )
    
    print("[WORKFLOW] Workflow compiled with interrupt_before=['human_approval']")
    return compiled


# -----------------------------
# Global workflow instance
# -----------------------------
_workflow = None

def get_workflow():
    """Get or create the workflow instance"""
    global _workflow
    if _workflow is None:
        _workflow = create_blog_workflow()
    return _workflow


# -----------------------------
# Blog Generator Functions (HITL Pattern)
# -----------------------------
def generate_blog(topic: str, thread_id: str) -> dict:
    """
    STEP 1: Start blog generation and STOP at human approval checkpoint
    This is the "before.py" equivalent - runs until interrupt
    Returns blog data in pending state
    """
    print(f"\n{'='*60}")
    print(f"[GENERATE] Starting blog generation (STEP 1: Before Human)")
    print(f"[GENERATE] Topic: {topic}")
    print(f"[GENERATE] Thread ID: {thread_id}")
    print(f"{'='*60}\n")
    
    workflow = get_workflow()

    initial_state: BlogState = {
        "topic": topic,
        "title": "",
        "outline": "",
        "content": "",
        "refined_content": "",
        "approval_status": "pending",
        "rejection_reason": ""
    }

    config = {"configurable": {"thread_id": thread_id}}
    
    # Run workflow - it will STOP at human_approval node (interrupt_before)
    print(f"[GENERATE] Invoking workflow (will pause at human_approval)...")
    result = workflow.invoke(initial_state, config)
    
    # Get current state to verify we're paused
    state = workflow.get_state(config)
    print(f"\n[GENERATE] ✓ Workflow paused at checkpoint")
    print(f"[GENERATE] Next node to execute: {state.next}")
    print(f"[GENERATE] Current approval status: {result.get('approval_status', 'pending')}")
    print(f"[GENERATE] Waiting for human decision via update_approval_status()...")
    
    return {
        "topic": result["topic"],
        "title": result["title"],
        "content": result["refined_content"],
        "approval_status": result.get("approval_status", "pending"),
        "thread_id": thread_id
    }


def update_approval_status(thread_id: str, action: str, rejection_reason: str = None) -> dict:
    """
    STEP 2 & 3: Update approval status and RESUME workflow
    This combines "human.py" and "after.py":
    - Updates state as if human_approval node executed (human.py)
    - Resumes execution from that point (after.py)
    """
    print(f"\n{'='*60}")
    print(f"[UPDATE] Human decision received (STEP 2: Human Input)")
    print(f"[UPDATE] Thread ID: {thread_id}")
    print(f"[UPDATE] Action: {action}")
    if rejection_reason:
        print(f"[UPDATE] Rejection reason: {rejection_reason}")
    print(f"{'='*60}\n")
    
    workflow = get_workflow()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get current state and verify we're at the checkpoint
    current_state = workflow.get_state(config)
    
    if current_state is None:
        raise ValueError(f"No workflow found for thread_id: {thread_id}")
    
    print(f"[UPDATE] Current state next nodes: {current_state.next}")
    print(f"[UPDATE] Verifying we're at human_approval checkpoint...")
    
    if current_state.next and "human_approval" not in str(current_state.next):
        print(f"[UPDATE] ⚠️ Warning: Not at expected checkpoint. Next: {current_state.next}")
    
    # Prepare the update values based on action
    if action == "approve":
        new_values = {"approval_status": "approved"}
        print(f"[UPDATE] Setting approval_status = 'approved'")
    elif action == "reject":
        new_values = {
            "approval_status": "rejected",
            "rejection_reason": rejection_reason or "No reason provided"
        }
        print(f"[UPDATE] Setting approval_status = 'rejected'")
    else:
        raise ValueError(f"Invalid action: {action}. Must be 'approve' or 'reject'")
    
    # Update state AS IF we're at the human_approval node
    # This is the key HITL pattern from the documentation
    print(f"[UPDATE] Calling update_state(as_node='human_approval')...")
    workflow.update_state(config, new_values, as_node="human_approval")
    
    # Verify the update
    updated_state = workflow.get_state(config)
    print(f"[UPDATE] ✓ State updated successfully")
    print(f"[UPDATE] Next nodes to execute: {updated_state.next}")
    print(f"[UPDATE] Updated approval_status: {updated_state.values.get('approval_status')}")
    
    # STEP 3: Resume execution from the checkpoint (after.py equivalent)
    print(f"\n{'='*60}")
    print(f"[RESUME] Resuming workflow execution (STEP 3: After Human)")
    print(f"{'='*60}\n")
    result = workflow.invoke(None, config)  # None = continue from checkpoint
    
    # Get final state
    final_state = workflow.get_state(config)
    print(f"\n[RESUME] ✓ Workflow completed")
    print(f"[RESUME] Final next nodes: {final_state.next}")
    print(f"[RESUME] Final approval status: {result.get('approval_status')}")
    print(f"{'='*60}\n")
    
    return {
        "topic": result["topic"],
        "title": result["title"],
        "content": result["refined_content"],
        "approval_status": result.get("approval_status", "pending"),
        "rejection_reason": result.get("rejection_reason", ""),
        "thread_id": thread_id
    }


def get_blog_state(thread_id: str) -> dict:
    """
    Get the current state of a blog workflow
    Useful for checking status without triggering execution
    """
    workflow = get_workflow()
    config = {"configurable": {"thread_id": thread_id}}
    
    state = workflow.get_state(config)
    
    if state is None:
        return None
    
    next_nodes = state.next if state.next else []
    
    return {
        "topic": state.values.get("topic", ""),
        "title": state.values.get("title", ""),
        "content": state.values.get("refined_content", ""),
        "approval_status": state.values.get("approval_status", "pending"),
        "rejection_reason": state.values.get("rejection_reason", ""),
        "next_nodes": next_nodes,
        "thread_id": thread_id
    }

