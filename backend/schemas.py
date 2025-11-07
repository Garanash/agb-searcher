from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    website: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    equipment_purchased: Optional[str] = None
    preferred_language: Optional[str] = None  # ru, en, de, fr, es, zh, ja

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    website: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    equipment_purchased: Optional[str] = None
    preferred_language: Optional[str] = None
    is_verified: Optional[bool] = None

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_verified: bool

    class Config:
        from_attributes = True

class EquipmentBase(BaseModel):
    name: str
    description: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class Equipment(EquipmentBase):
    id: int
    companies_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str

class CompanySearchResult(BaseModel):
    name: str
    website: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    equipment: Optional[str] = None
    preferred_language: Optional[str] = None

class EquipmentSearchResult(BaseModel):
    companies: List[CompanySearchResult]
    equipment_name: str
    total_found: int

class FileUploadResponse(BaseModel):
    message: str
    companies_processed: int
    companies_found: int

class AssistantBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    model: str = "gpt-4o"
    temperature: Optional[str] = "0.7"
    max_tokens: int = 2000

class AssistantCreate(AssistantBase):
    pass

class AssistantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None

class Assistant(AssistantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmailCampaignCreate(BaseModel):
    subject: str
    body: str
    company_ids: Optional[List[int]] = None

class EmailCampaign(BaseModel):
    id: int
    subject: str
    body: str
    company_ids: Optional[List[int]] = None
    sent_count: int
    failed_count: int
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmailVerificationRequest(BaseModel):
    email: str
    company_id: Optional[int] = None

class EmailVerification(BaseModel):
    id: int
    email: str
    company_id: Optional[int] = None
    is_valid: bool
    is_deliverable: bool
    verification_status: str
    last_checked: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class AgentActionRequest(BaseModel):
    action: str  # search_company, save_company, navigate_to_page, etc.
    parameters: dict

class AgentActionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
