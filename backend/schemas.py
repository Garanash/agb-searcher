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

class ChatMessage(BaseModel):
    role: str  # "user" или "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    message: str
    conversation_history: List[ChatMessage]

class DialogBase(BaseModel):
    title: str

class DialogCreate(DialogBase):
    pass

class DialogUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None

class Dialog(DialogBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class DialogMessageBase(BaseModel):
    role: str
    content: str

class DialogMessageCreate(DialogMessageBase):
    dialog_id: int

class DialogMessage(DialogMessageBase):
    id: int
    dialog_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DialogWithMessages(Dialog):
    messages: List[DialogMessage] = []

class ChatRequestWithDialog(BaseModel):
    message: str
    dialog_id: Optional[int] = None
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponseWithDialog(BaseModel):
    message: str
    conversation_history: List[ChatMessage]
    dialog_id: int

class DialogSettingsBase(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = "gpt-4o"
    temperature: Optional[str] = "0.7"
    max_tokens: Optional[int] = 1000

class DialogSettingsCreate(DialogSettingsBase):
    pass

class DialogSettingsUpdate(DialogSettingsBase):
    pass

class DialogSettings(DialogSettingsBase):
    id: int
    dialog_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AssistantBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    model: str = "gpt-4o"
    temperature: Optional[str] = "0.7"
    max_tokens: Optional[int] = 1000

class AssistantCreate(AssistantBase):
    pass

class AssistantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None

class Assistant(AssistantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DialogFileBase(BaseModel):
    filename: str
    file_type: Optional[str] = None
    content: Optional[str] = None

class DialogFileCreate(DialogFileBase):
    dialog_id: int

class DialogFile(DialogFileBase):
    id: int
    dialog_id: int
    file_path: str
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DialogWithSettings(Dialog):
    settings: Optional[DialogSettings] = None
    files: List[DialogFile] = []