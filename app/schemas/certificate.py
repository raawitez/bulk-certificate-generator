from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CertificateResponse(BaseModel):
    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

class PaginatedCertificateResponse(BaseModel):
    items: List[CertificateResponse]
    page: int
    page_size: int
    total: int