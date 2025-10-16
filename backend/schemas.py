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

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    website: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    equipment_purchased: Optional[str] = None
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

class EquipmentSearchResult(BaseModel):
    companies: List[CompanySearchResult]
    equipment_name: str
    total_found: int

class FileUploadResponse(BaseModel):
    message: str
    companies_processed: int
    companies_found: int
