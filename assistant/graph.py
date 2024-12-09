from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from assistant.state import State, CaseData, UserData, CaseFiles, get_schema_json
from langchain_core.runnables import RunnableConfig
from assistant.configuration import FireStore, Memory, store
from assistant import configuration
from langgraph.graph import END, StateGraph
from trustcall import create_extractor
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import List, Dict, Any
from assistant import prompts
from datetime import datetime       
import logging
import uuid
import json
import os

# Initialize the configuration
CONFIG = configuration.Configuration.from_runnable_config({
    "configurable": {
        "model": os.getenv("OPENAI_API_KEY", "gpt-4")
    }
})
CASE_ID = CONFIG.case_id
LLM = CONFIG.model
TOOLS = [
    process_files,
    update_case,
    update_user
]

async def case_manager(state: State, store: FireStore = store) -> dict:
    """Manages the case intake interview process."""
    existing_data = {
        "case_data": json.dumps(state.case_data.model_dump(), indent=2)
    }

    case_manager_prompt = CONFIG.case_manager_prompt.format(
        data_schema=get_schema_json(state.case_data),
        existing_data=existing_data
    )
    filtered_messages = [
        msg for msg in state.messages 
        if isinstance(msg, (HumanMessage, AIMessage))
    ]
    next_question = await LLM.ainvoke(
        [SystemMessage(content=case_manager_prompt), *filtered_messages]
    )
    return {"messages":[
        AIMessage(content=next_question)
    ]}
    
async def end_interview(state: State) -> dict:
    """Ends the interview session."""
    return {"messages": [
        *state.messages, 
        AIMessage(
            content="Thank you for your time. The interview is now complete."
        )
    ]}

async def router_node(state: State) -> str:
    """Routes the conversation flow."""
    msg = state.messages[-1]
    
    if isinstance(msg, HumanMessage) and msg.content.lower() in ["quit", "exit", "terminate"]:
        return "end_interview"
    
    if msg.additional_kwargs.get("tool_calls"):
        tool_names = [tc["function"]["name"] for tc in msg.additional_kwargs["tool_calls"]]
        if "UserData" in tool_names:
            return "update_user"
        if "CaseData" in tool_names:
            return "update_case"
    return "case_manager"

# Create the graph
builder = StateGraph(State, config_schema=configuration.Configuration)

# Add nodes
builder.add_node("case_manager", case_manager)
builder.add_node("update_case", update_case)
builder.add_node("update_user", update_user)
builder.add_node("end_interview", end_interview)

# Set the entry point
builder.add_edge("__start__", "case_manager")

# Add conditional edges
builder.add_conditional_edges(
    "case_manager",
    router_node,
    {
        "update_case": "update_case",
        "update_user": "update_user",
        "end_interview": "end_interview",
        END: END
    }
)

# Add edge from end_interview to END
builder.add_edge("end_interview", END)

# Compile the graph
assistant = builder.compile()
assistant.name = "CaseManagerAgent"

__all__ = ["assistant"]

