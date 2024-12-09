import uuid
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_core.prompts import SystemMessage
from langchain_core.pydantic_v1 import BaseModel
from trustcall import create_extractor
from assistant.graph import CASE_ID, LLM
from assistant.state import State, CaseData, UserData, get_schema_json
from assistant.prompts import prompts
from assistant.configuration import Configuration, FireStore, Memory, store

async def update_case(state: State, store: FireStore = store) -> dict:
    """Updates case data in Firestore."""
    # Get existing case data
    case_docs = await store.get(('cases', CASE_ID))
    existing_case_data = case_docs.data if case_docs else {}
    
    case_trustcall = create_extractor(
        llm=LLM,
        tools=[CaseData],
        tool_choice="CaseData",
        enable_insert=True
    )
    case_trustcall_prompt = prompts.TRUSTCALL_INSTRUCTION.format(
        data_schema=get_schema_json(CaseData),
        existing_data=State.case_data.model_dump_json(indent=2),
    )
    updated_messages = [
        SystemMessage(content=case_trustcall_prompt),
        *state.messages[:-1]
    ]
    updated_case_data = await case_trustcall.ainvoke({
        "messages": updated_messages, 
        "existing": existing_case_data
    })  
    
    await store.batch()
    for r, rmeta in zip(updated_case_data["responses"], updated_case_data["response_metadata"]):
        data = r.model_dump(mode="json")
        doc_id = rmeta.get("doc_id", str(uuid.uuid4()))
    
        # Handle nested models
        for field_name, field_value in data.items():
            if isinstance(field_value, dict) and hasattr(CaseData, field_name):
                field_type = getattr(CaseData, field_name).type_
                if issubclass(field_type, BaseModel):
                    # Store in subcollection
                    subcoll_memory = Memory(
                        collection=f'cases/{CASE_ID}/{field_name}',
                        document_id=doc_id,
                        data=field_value
                    )
                    await store.set((subcoll_memory.collection, subcoll_memory.document_id), subcoll_memory)
                    data[field_name] = f"ref:{doc_id}"
        
        # Store main document
        case_data_memory = Memory(
            collection='case-data',
            document_id=CASE_ID,
            data=data
        )
        await store.set((case_data_memory.collection, case_data_memory.document_id), case_data_memory)
    
    await store.commit()
    return {"messages": [
        ToolMessage(
            content="Case data updated", 
            tool_call_id=str(uuid.uuid4())
        )
    ]}

@tool('update_user')
async def update_user(state: State, store: FireStore = store) -> dict:
    """Updates user data in Firestore."""
    # Get existing user data
    user_docs = await store.get(('users', CASE_ID))
    existing_user_data = user_docs.data if user_docs else {}
    
    user_trustcall = create_extractor(
        llm=LLM,
        tools=[UserData],
        tool_choice="UserData",
        enable_insert=True
    )
    user_trustcall_prompt = prompts.TRUSTCALL_INSTRUCTION.format(
        data_schema=get_schema_json(State.user),
    )
    updated_messages = [
        SystemMessage(content=user_trustcall_prompt),
        *state.messages[:-1]
    ]
    extracted_user_data = await user_trustcall.ainvoke({
        "messages": updated_messages, 
        "existing": existing_user_data
    })  
    
    # Create and store user memory
    user_data_memory = Memory(
        collection='users',
        document_id=CASE_ID,
        data=extracted_user_data["responses"][0].model_dump(mode='json')
    )
    await store.set((user_data_memory.collection, user_data_memory.document_id), user_data_memory)
    
    return {"messages": [
        ToolMessage(
            content="User data updated", 
            tool_call_id=str(uuid.uuid4())
        )
    ]}
