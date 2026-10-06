from pydantic import BaseModel, Field
from typing import List

class RecipientInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Recipient's full name")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="Valid email address")

class JobCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=200)
    event_date: str = Field(..., description="Date string, e.g., 2026-10-10")
    certificate_title: str = Field(..., min_length=1, max_length=200)
    recipients: List[RecipientInfo] = Field(..., min_length=1, max_length=5000)

class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    total: int

class JobStatusResponse(BaseModel):
    job_id: str
    event_name: str
    status: str
    total: int
    successful: int
    failed: int
    pending: int
    progress_percentage: float