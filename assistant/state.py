"""Define the shared values."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated
import uuid

class UserData(BaseModel):
    """Personal information of the client"""
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    age: Optional[int] = Field(default=None)
    gender: str = Field(default="")
    date_of_birth: Optional[date] = Field(default=None)
    home_address: str = Field(default="")
    email: str = Field(default="")
    phone: str = Field(default="")
    preferred_contact_method: Optional[str] = Field(default=None)

@dataclass(kw_only=True)
class IncidentDetails(BaseModel):
    """Details about the incident including time, date, location, and description"""
    incident_date: datetime = Field('', description="Time and date of the incident", examples=["2024-01-01 10:00:00", "2024-02-01 14:30:00"])
    incident_time: str = Field('', description="Time of day of the incident", examples=["morning", "afternoon", "evening", "night"])
    incident_location: str = Field('', description="Location of the incident", examples=["123 Main St, Anytown, USA", "456 Elm St, Othertown, USA"])
    incident_description: str = Field('', description="Description of the incident", examples=["I was walking down the street and a car hit me", "I was at work and a machine malfunctioned and injured me", "I was at a friend's house and slipped and fell"])
    incident_type: str = Field('', description="Type of the incident", examples=["workplace", "car accident", "slip and fall", "medical malpractice", "product liability", "other"])

@dataclass(kw_only=True)
class WitnessInfo(BaseModel):
    """Information about any witnesses to the incident including their contact details and statement"""
    name: Optional[str] = Field(None, description="Witness's full name if provided", examples=["John Smith", "Mary Wilson"])
    contact_info: Optional[str] = Field(None, description="Witness's contact information if provided", examples=["(555) 123-4567", "john.smith@email.com"])
    relationship: Optional[str] = Field(None, description="Witness's relationship to the client if provided", examples=["Friend", "Coworker", "Neighbor"])
    statement: Optional[str] = Field(None, description="Witness's statement if provided", examples=["I saw the accident happen", "I was with the client when it happened"])

@dataclass(kw_only=True)
class InjuryDetails(BaseModel):
    """Details about the injury including symptoms, severity, duration, and impact"""
    list_injury_details: List[str] = Field('', description="List of all injuries", examples=["I have a sprained ankle", "I have a broken arm", "I have a concussion"])
    symptom_details: List[str] = Field('', description="Details about each symptom", examples=["I have pain in my ankle", "I have swelling in my arm", "I have dizziness"])
    injury_severity: str = Field('', description="Severity of the injury", examples=["minor", "moderate", "severe"])
    injury_duration: str = Field('', description="Duration of the injury", examples=["I have had this injury for 2 days", "I have had this injury for 2 weeks", "I have had this injury for 2 months"])
    injury_impact: str = Field('', description="Impact of the injury", examples=["I am unable to work", "I am unable to walk", "I am unable to move my arm"])

@dataclass(kw_only=True)
class MedicalInfo(BaseModel):
    """Medical treatment history including facilities, doctors, and current/future treatment plans"""
    initial_treatment: str = Field('', description="Initial medical treatment received", examples=["Went to ER", "Saw primary care doctor next day"])
    treatment_facilities: List[str] = Field('', description="Medical facilities visited", examples=["Memorial Hospital", "City Medical Center"])
    treating_physicians: List[str] = Field('', description="Names of treating doctors", examples=["Dr. Smith", "Dr. Jones"])
    current_treatment: str = Field('', description="Current treatment status", examples=["Physical therapy 2x/week", "No current treatment"])
    future_treatment_needed: Optional[str] = Field(None, description="Planned future treatment", examples=["Surgery scheduled", "Ongoing physical therapy needed"])
    pre_existing_conditions: Optional[str] = Field(None, description="Extract relevant pre-existing conditions", examples=["Prior back injury", "No pre-existing conditions"])
    medications: Optional[List[str]] = Field(None, description="Medications prescribed", examples=["Ibuprofen", "Muscle relaxers"])

@dataclass(kw_only=True)
class InsurancePolicy(BaseModel):
    """Insurance policy information including policy number, provider, and coverage details"""
    company_name: str = Field('', description="Insurance company name", examples=["Blue Cross Blue Shield", "United Healthcare"])
    policy_number: str = Field('', description="Insurance policy number", examples=["1234567890", "0987654321"])
    policy_holder_name: str = Field('', description="Name of the policy holder", examples=["John Doe", "Jane Smith"])
    coverage_details: str = Field('', description="Coverage details", examples=["$100,000 per accident", "50% coverage for medical expenses"])
    policy_start_date: date = Field('', description="Date when the policy was started", examples=["2024-01-01", "2024-02-01"])
    policy_end_date: date = Field('', description="Date when the policy was ended", examples=["2024-01-01", "2024-02-01"])
    policy_type: str = Field('', description="Type of the policy", examples=["Health", "Life", "Auto", "Home", "Other"])
    policy_status: str = Field('', description="Status of the policy", examples=["Active", "Inactive", "Pending", "Other"])

@dataclass(kw_only=True)
class InsuranceInfo(BaseModel):
    """Insurance information including policy number, provider, and coverage details"""
    client_insurance: InsurancePolicy = Field(default_factory=InsurancePolicy, description="Insurance policy information")
    insurance_notified: bool = Field('', description="Whether the insurance company has been notified", examples=[True, False])
    notification_date: Optional[date] = Field(None, description="Date when the insurance company was notified", examples=["2024-01-01", "2024-02-01"])
    claim_number: Optional[str] = Field(None, description="Insurance claim number", examples=["1234567890", "0987654321"])
    claim_status: Optional[str] = Field(None, description="Status of the claim", examples=["Pending", "In Progress", "Closed"]) 

@dataclass(kw_only=True)
class EmployerInfo(BaseModel):
    """Information about the client's employer including employer name, position, and employment details"""
    company_name: str = Field('', description="Employer", examples=["Acme Inc.", "XYZ Corp."])
    address: str = Field('', description="Address of the employer", examples=["123 Main St, Anytown, USA", "456 Elm St, Othertown, USA"])
    phone: str = Field('', description="Phone number of the employer", examples=["(555) 123-4567", "123-456-7890"])

@dataclass(kw_only=True)
class EmploymentInfo(BaseModel):
    """Employment information including employer, position, and employment details"""
    current_employer: EmployerInfo = Field(default_factory=EmployerInfo, description="Current employer information")
    employment_status_at_incident: str = Field('', description="Employment status at the time of the incident", examples=["Employed", "Unemployed", "Retired", "Student", "Other"])
    employment_type: str = Field('', description="Employment type", examples=["Full-time", "Part-time", "Temporary"])
    position: str = Field('', description="Position", examples=["Software Engineer", "Sales Associate"])
    work_missed: str = Field('', description="Whether the client missed work due to the injury", examples=[True, False])
    income_loss: str = Field('', description="Whether the client has experienced a loss of income due to the injury", examples=[True, False])
    work_restrictions: str = Field('', description="Whether the client has restrictions on their work due to the injury", examples=['unable to work', 'able to work but with limitations like lifting', 'other'])

@dataclass(kw_only=True)
class DamagesInfo(BaseModel):
    """Financial impact of the incident including medical costs, property damage and lost wages"""
    medical_expenses: Optional[float] = Field(None, description="Total medical expenses incurred", examples=[5000.00, 12500.50])
    property_damage: Optional[float] = Field(None, description="Total property damage costs", examples=[2000.00, 15000.00])
    lost_wages: Optional[float] = Field(None, description="Total lost wages amount", examples=[3000.00, 8000.00])
    other_expenses: Optional[Dict[str, float]] = Field(None, description="Any other expenses with descriptions", examples=[{"Transportation": 500.00, "Home care": 1200.00}])
    future_expenses: Optional[str] = Field(None, description="Anticipated future expenses", examples=["Ongoing physical therapy estimated at $200/week", "Future surgery estimated at $25,000"])

@dataclass(kw_only=True)
class LegalInfo(BaseModel):
    """Legal aspects of the case including prior representation, documents and settlement information"""
    prior_attorneys: Optional[str] = Field(None, description="Information about any previous attorneys consulted", examples=["Consulted with Smith & Jones but didn't retain", "None"])
    signed_documents: Optional[str] = Field(None, description="Details about legal documents already signed", examples=["Signed medical release forms", "Insurance statement on 2024-01-15"])
    legal_deadlines: Optional[str] = Field(None, description="Relevant legal deadlines or statutes of limitations", examples=["Statute of limitations expires 2025-06-01", "Insurance claim deadline in 30 days"])
    settlement_offers: Optional[str] = Field(None, description="Information about any settlement offers received", examples=["Initial offer of $25,000 received on 2024-02-01", "No offers yet"])
    desired_outcome: Optional[str] = Field(None, description="Client's desired outcome or settlement expectations", examples=["Seeking compensation for all medical bills plus lost wages", "Fair settlement to cover future treatment"])

@dataclass(kw_only=True)
class CaseFiles(BaseModel):
    """Metadata about a file uploaded by the user"""
    file_id: str = Field('', description="Unique identifier for the file", examples=["1234567890", "0987654321"])
    file_type: str = Field('', description="Type of the file", examples=["pdf", "image"])    
    file_name: str = Field('', description="Based on your analysis create a unique filename for the file", examples=["insurance_statement.pdf", "car_damage.jpg"])
    file_size: int = Field('', description="Size of the file in bytes", examples=[1024, 1024000])
    file_label: str = Field('', description="Tagline for the file", examples=["Statement from the insurance company", "Picture of the car damage"])
    file_analysis: str = Field('', description="an indepth analysis of the file contents and relevant details generated by an LLM")
    image_url: Optional[str] = Field(None, description="URL of the image if the file is an image", examples=["https://example.com/image.jpg"])
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Date and time when the file was uploaded")
    file_contents: str = Field('', description="The text contents of the file as a string")

@dataclass(kw_only=True)
class CaseData(BaseModel):
    """Complete state of a client's case and interview including all pertinent details and conversation history.
    Manages the overall state of a legal case, tracking all information from initial intake through case progression."""
    intake_date: date = Field(default_factory=date.today)
    user_data: UserData = Field(default_factory=UserData)
    documents: List[CaseFiles] = Field(default_factory=list)
    incident_details: Optional[IncidentDetails] = Field(default=None)
    witness_info: Optional[WitnessInfo] = Field(default=None)
    injury_details: Optional[InjuryDetails] = Field(default=None)
    medical_info: Optional[MedicalInfo] = Field(default=None)
    insurance_info: Optional[InsuranceInfo] = Field(default=None)
    employment_info: Optional[EmploymentInfo] = Field(default=None)
    damages_info: Optional[DamagesInfo] = Field(default=None)
    legal_info: Optional[LegalInfo] = Field(default=None)
    case_files: List[CaseFiles] = Field(default_factory=list)
    case_report: str = Field(default="")
    report_status: str = Field(default="Not_sent")

def get_schema_json():
    schema_json = CaseData.model_json_schema()
    if "title" in schema_json:
        del schema_json["title"]
    if "$defs" in schema_json:
        del schema_json["$defs"]
    return schema_json

@dataclass(kw_only=True)
class State:    
    """Main graph state."""
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_data: CaseData = field(default_factory=lambda: CaseData.model_validate({}))
    user_data: UserData = field(default_factory=lambda: UserData.model_validate({}))
    messages: Annotated[list[AnyMessage], add_messages] = field(default_factory=list)

__all__ = [
    "State"
    ]
