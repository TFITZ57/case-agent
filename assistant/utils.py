"""Utility functions used in our graph."""

from typing import List, Dict, Any
from configuration import Memory, db, conf
import uuid     
from datetime import datetime
from langchain.schema import SystemMessage, HumanMessage
from PIL import Image
import pytesseract
import fitz 
import io
import json

from memory_agent import configuration

def split_model_and_provider(fully_specified_name: str) -> dict:
    """Initialize the configured chat model."""
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = None
        model = fully_specified_name
    return {"model": model, "provider": provider}


async def file_analysis(file: Dict[str, Any], model: Any) -> Dict[str, Any]:
    """Extract text and analyze content from different file types"""
    
    content = file.get("content")
    file_type = file.get("type")
    
    if not content:
        return {"error": "No content provided"}

    extracted_text = ""
    try:
        if file_type.startswith('image'):
            # Handle image files
            if isinstance(content, Image.Image):
                # Extract text from image using OCR
                extracted_text = pytesseract.image_to_string(content)
                
                # Get image analysis from vision model
                vision_response = await model.ainvoke([
                    SystemMessage(content="Analyze this image and extract all relevant case information. Focus on visible damages, injuries, documents, or other pertinent details."),
                    HumanMessage(content=[
                        {"type": "text", "text": "describe the image in detail?"},
                        {"type": "image_url", "image_url": content}
                    ])
                ])
                extracted_text += f"\nImage Analysis: {vision_response.content}"
                
        elif file_type == 'application/pdf':
            # Handle PDF files
            pdf_doc = fitz.open(stream=content, filetype="pdf")
            for page in pdf_doc:
                extracted_text += page.get_text()
            pdf_doc.close()
            
        else:
            # Handle text-based documents
            if isinstance(content, bytes):
                extracted_text = content.decode('utf-8')
            else:
                extracted_text = str(content)
    
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}

    return {
        "extracted_text": extracted_text,
        "file_type": file_type,
        "processed_at": datetime.now().isoformat()
    }
