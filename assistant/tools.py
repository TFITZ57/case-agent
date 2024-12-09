import uuid
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langchain_core.prompts import SystemMessage
from langchain_core.pydantic_v1 import BaseModel
from trustcall import create_extractor
from assistant.graph import CASE_ID, LLM
from assistant.state import State, CaseData, UserData, get_schema_json, CaseFiles
from assistant.prompts import prompts
from assistant.configuration import Configuration, FireStore, Memory, store
from typing import List, Dict, Any, Optional
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import io
import json
from datetime import datetime

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

@tool("process_files")
async def process_files(state: State, files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process uploaded files and extract relevant information."""
    processed_files = []
    
    for file in files:
        try:
            file_id = str(uuid.uuid4())
            file_content = file.get("content")
            file_type = file.get("type", "")
            file_name = file.get("name", "")
            
            # Extract text based on file type
            extracted_text = ""
            if file_type.startswith('image'):
                image = Image.open(io.BytesIO(file_content))
                extracted_text = pytesseract.image_to_string(image)
            elif file_type == 'application/pdf':
                pdf = fitz.open(stream=file_content, filetype="pdf")
                for page in pdf:
                    extracted_text += page.get_text()
                pdf.close()
            else:
                extracted_text = file_content.decode('utf-8')
            
            # Create file metadata
            file_metadata = CaseFiles(
                file_id=file_id,
                file_type=file_type,
                file_name=file_name,
                file_size=len(file_content),
                file_label=f"Uploaded {file_type} document",
                uploaded_at=datetime.now(),
                file_contents=extracted_text
            )
            
            # Store file in database
            await store.set(
                ('files', file_id),
                {
                    "metadata": file_metadata.model_dump(),
                    "content": file_content
                }
            )
            
            processed_files.append(file_metadata)
            
            # Update case data with new file
            if state.case_data.documents is None:
                state.case_data.documents = []
            state.case_data.documents.append(file_metadata)
            
        except Exception as e:
            return {"error": f"Error processing file {file_name}: {str(e)}"}
    
    return {
        "processed_files": [f.model_dump() for f in processed_files],
        "case_data": state.case_data
    }

@tool("analyze_document")
async def analyze_document(state: State, file_id: str) -> Dict[str, Any]:
    """Analyze a document to extract case-relevant information."""
    try:
        # Get file from database
        file_data = await store.get(('files', file_id))
        if not file_data:
            return {"error": "File not found"}
        
        file_metadata = CaseFiles(**file_data["metadata"])
        
        # Analyze content with LLM
        analysis_prompt = f"""
        Analyze this document and extract any relevant case information:
        
        {file_metadata.file_contents}
        
        Focus on:
        1. Dates and times
        2. Names and contact information
        3. Incident details
        4. Medical information
        5. Insurance details
        6. Financial information
        """
        
        analysis_result = await state.llm.ainvoke([
            SystemMessage(content=analysis_prompt)
        ])
        
        # Update file metadata with analysis
        file_metadata.file_analysis = analysis_result.content
        
        # Store updated metadata
        await store.set(
            ('files', file_id),
            {
                "metadata": file_metadata.model_dump(),
                "content": file_data["content"]
            }
        )
        
        return {
            "file_id": file_id,
            "analysis": analysis_result.content
        }
        
    except Exception as e:
        return {"error": f"Error analyzing document: {str(e)}"}

@tool("get_document")
async def get_document(state: State, file_id: str) -> Dict[str, Any]:
    """Retrieve a document from the database."""
    try:
        file_data = await store.get(('files', file_id))
        if not file_data:
            return {"error": "File not found"}
            
        return {
            "metadata": file_data["metadata"],
            "content": file_data["content"]
        }
        
    except Exception as e:
        return {"error": f"Error retrieving document: {str(e)}"}
