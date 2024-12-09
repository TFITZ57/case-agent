import streamlit as st
from assistant.graph import assistant
from assistant.state import State, CaseData, UserData
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from assistant.configuration import firebase_app, firestore_db
from assistant import prompts
import asyncio
from typing import List, Dict, Any
import json
import os
from dotenv import load_dotenv
from datetime import date, datetime

# Load environment variables
load_dotenv()

# Set up the page
st.set_page_config(page_title="Legal Case Intake Assistant", layout="wide")
st.title("Legal Case Intake Assistant")

# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = State()
    st.session_state.messages = st.session_state.state.messages
    st.session_state.case_data = st.session_state.state.case_data
    st.session_state.user_data = st.session_state.state.user_data
    
    # Add initial disclaimer message
    st.session_state.messages.append(
        AIMessage(content=prompts.DISCLAIMER)
    )

# Sidebar for file uploads and case info
with st.sidebar:
    st.header("Case Documents")
    uploaded_files = st.file_uploader("Upload relevant documents", 
                                    accept_multiple_files=True,
                                    type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_files:
        for file in uploaded_files:
            try:
                file_content = file.read()
                human_msg = HumanMessage(content=f"I'm uploading a file named {file.name}")
                st.session_state.messages.append(human_msg)
            except Exception as e:
                st.error(f"Error processing file {file.name}: {str(e)}")

    # Display current case data
    st.header("Case Information")
    case_data = st.session_state.case_data

    with st.expander("📋 Basic Information", expanded=True):
        st.write(f"**Case ID:** {case_data.case_id}")
        st.write(f"**Intake Date:** {case_data.intake_date}")
        
        if case_data.user_data:
            st.subheader("👤 Client Information")
            user = case_data.user_data
            if user.first_name or user.last_name:
                st.write(f"**Name:** {user.first_name} {user.last_name}")
            if user.email:
                st.write(f"**Email:** {user.email}")
            if user.phone:
                st.write(f"**Phone:** {user.phone}")
            if user.preferred_contact_method:
                st.write(f"**Preferred Contact:** {user.preferred_contact_method}")

    with st.expander("🚨 Incident Details"):
        if case_data.incident_details:
            incident = case_data.incident_details
            st.write(f"**Date:** {incident.incident_date}")
            st.write(f"**Type:** {incident.incident_type}")
            st.write(f"**Location:** {incident.incident_location}")
            if incident.incident_description:
                st.write("**Description:**")
                st.write(incident.incident_description)
        else:
            st.info("No incident details provided yet")

    with st.expander("🏥 Medical Information"):
        if case_data.medical_info:
            medical = case_data.medical_info
            if medical.initial_treatment:
                st.write(f"**Initial Treatment:** {medical.initial_treatment}")
            if medical.treatment_facilities:
                st.write("**Facilities:**")
                for facility in medical.treatment_facilities:
                    st.write(f"- {facility}")
            if medical.current_treatment:
                st.write(f"**Current Treatment:** {medical.current_treatment}")
        else:
            st.info("No medical information provided yet")

    with st.expander("💰 Damages & Insurance"):
        if case_data.damages_info:
            damages = case_data.damages_info
            if damages.medical_expenses:
                st.write(f"**Medical Expenses:** ${damages.medical_expenses:,.2f}")
            if damages.lost_wages:
                st.write(f"**Lost Wages:** ${damages.lost_wages:,.2f}")
            if damages.property_damage:
                st.write(f"**Property Damage:** ${damages.property_damage:,.2f}")
        else:
            st.info("No damages information provided yet")
        
        if case_data.insurance_info:
            insurance = case_data.insurance_info
            if insurance.client_insurance:
                st.write("**Insurance Information:**")
                st.write(f"- Company: {insurance.client_insurance.company_name}")
                st.write(f"- Policy #: {insurance.client_insurance.policy_number}")
        else:
            st.info("No insurance information provided yet")

    with st.expander("📄 Documents"):
        if case_data.documents:
            for doc in case_data.documents:
                st.write(f"- {doc.file_name} ({doc.file_type})")
        else:
            st.info("No documents uploaded yet")

    with st.expander("⚖️ Legal Status"):
        st.write(f"**Report Status:** {case_data.report_status}")
        if case_data.legal_info:
            legal = case_data.legal_info
            if legal.prior_attorneys:
                st.write(f"**Prior Attorneys:** {legal.prior_attorneys}")
            if legal.legal_deadlines:
                st.write(f"**Important Deadlines:** {legal.legal_deadlines}")
        else:
            st.info("No legal information provided yet")

# Chat interface
chat_container = st.container()

# Add custom CSS for message alignment
st.markdown("""
<style>
.user-message {
    margin-left: 20%;
    margin-right: 2%;
}
.assistant-message {
    margin-right: 20%;
    margin-left: 2%;
}
div[data-testid="stHorizontalBlock"] {
    gap: 0px;
}
</style>
""", unsafe_allow_html=True)

# Display chat messages
with chat_container:
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if isinstance(msg, HumanMessage):
                col1, col2 = st.columns([4, 1])
                with col2:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(msg.content)
            elif isinstance(msg, AIMessage):
                col1, col2 = st.columns([1, 4])
                with col1:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg.content)
            elif isinstance(msg, ToolMessage):
                continue
    else:
        st.info("Start a conversation by typing a message below! 👇")

# User input area with placeholder text
user_input = st.chat_input("Type your message here...", key="user_input")

async def process_message(message: str) -> None:
    """Process a message through the assistant."""
    try:
        # Add user message
        human_msg = HumanMessage(content=message)
        st.session_state.messages.append(human_msg)
        
        # Get response from assistant
        result = await assistant.ainvoke(st.session_state.state)
        
        # Update session state with new messages
        st.session_state.messages.extend(result["messages"])
        
        # Update case data if present
        if "case_data" in result:
            st.session_state.case_data = result["case_data"]
            st.session_state.state.case_data = result["case_data"]
        
        # Update user data if present
        if "user_data" in result:
            st.session_state.user_data = result["user_data"]
            st.session_state.state.user_data = result["user_data"]
            
    except Exception as e:
        st.error(f"Error processing message: {str(e)}")

# Process user input
if user_input:
    try:
        asyncio.run(process_message(user_input))
        # Force a rerun to update the UI
        st.rerun()
    except Exception as e:
        st.error(f"Error processing input: {str(e)}")

# Add a clear chat button
if st.button("Clear Chat"):
    try:
        st.session_state.state = State()
        st.session_state.messages = st.session_state.state.messages
        st.session_state.case_data = st.session_state.state.case_data
        st.session_state.user_data = st.session_state.state.user_data
        st.rerun()
    except Exception as e:
        st.error(f"Error clearing chat: {str(e)}")

# Cleanup temporary credentials file
try:
    if os.path.exists(os.getenv("FIREBASE_CREDENTIALS_PATH", "")):
        os.unlink(os.getenv("FIREBASE_CREDENTIALS_PATH"))
except Exception:
    pass