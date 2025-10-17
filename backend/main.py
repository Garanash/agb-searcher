from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
import asyncio
from datetime import datetime

from database import get_db, create_tables, Company, Equipment, SearchLog, Dialog, DialogMessage, DialogSettings, Assistant, DialogFile
from schemas import (
    Company as CompanySchema, 
    CompanyCreate, 
    CompanyUpdate,
    Equipment as EquipmentSchema,
    EquipmentCreate,
    SearchRequest,
    CompanySearchResult,
    EquipmentSearchResult,
    FileUploadResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    Dialog,
    DialogCreate,
    DialogUpdate,
    DialogWithMessages,
    DialogMessage,
    DialogMessageCreate,
    ChatRequestWithDialog,
    ChatResponseWithDialog,
    DialogSettings,
    DialogSettingsCreate,
    DialogSettingsUpdate,
    Assistant,
    AssistantCreate,
    AssistantUpdate,
    DialogFile,
    DialogFileCreate,
    DialogWithSettings
)
from polza_client import PolzaAIClient

app = FastAPI(title="AGB Searcher API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание таблиц при запуске
create_tables()

polza_client = PolzaAIClient()

@app.get("/")
async def root():
    return {"message": "AGB Searcher API работает!"}

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {"status": "healthy", "service": "agb-searcher-backend"}

@app.get("/companies", response_model=List[CompanySchema])
async def get_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех компаний"""
    companies = db.query(Company).offset(skip).limit(limit).all()
    return companies

@app.get("/companies/{company_id}", response_model=CompanySchema)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Получить информацию о конкретной компании"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return company

@app.put("/companies/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: int, 
    company_update: CompanyUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить информацию о компании"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    
    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    return company

@app.post("/companies/search", response_model=CompanySearchResult)
async def search_company_info(
    search_request: SearchRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Поиск информации о компании через Polza.AI"""
    company_name = search_request.query.strip()
    
    if not company_name:
        raise HTTPException(status_code=400, detail="Название компании не может быть пустым")
    
    # Логируем поиск
    search_log = SearchLog(
        search_type="company",
        query=company_name,
        results_count=0
    )
    db.add(search_log)
    db.commit()
    
    # Поиск через Polza.AI
    company_info = await polza_client.search_company_info(company_name)
    
    # Обновляем лог
    search_log.results_count = 1 if company_info else 0
    db.commit()
    
    if not company_info:
        raise HTTPException(status_code=500, detail="Ошибка при обращении к внешнему API. Попробуйте позже.")
    
    return CompanySearchResult(
        name=company_name,
        website=company_info.get("website", ""),
        email=company_info.get("email", ""),
        address=company_info.get("address", ""),
        phone=company_info.get("phone", ""),
        description=company_info.get("description", ""),
        equipment=company_info.get("equipment", "")
    )

@app.post("/equipment/search", response_model=EquipmentSearchResult)
async def search_companies_by_equipment(
    search_request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Поиск компаний, которые купили определенное оборудование"""
    equipment_name = search_request.query.strip()
    
    if not equipment_name:
        raise HTTPException(status_code=400, detail="Название оборудования не может быть пустым")
    
    # Логируем поиск
    search_log = SearchLog(
        search_type="equipment",
        query=equipment_name,
        results_count=0
    )
    db.add(search_log)
    db.commit()
    
    # Поиск через Polza.AI
    companies_data = await polza_client.search_companies_by_equipment(equipment_name)
    
    # Обновляем лог
    search_log.results_count = len(companies_data)
    db.commit()
    
    companies = []
    for company_data in companies_data:
        companies.append(CompanySearchResult(
            name=company_data.get("name", ""),
            website=company_data.get("website", ""),
            email=company_data.get("email", ""),
            address=company_data.get("address", ""),
            phone=company_data.get("phone", ""),
            description=company_data.get("description", ""),
            equipment=equipment_name
        ))
    
    return EquipmentSearchResult(
        companies=companies,
        equipment_name=equipment_name,
        total_found=len(companies)
    )

@app.post("/companies/bulk-search", response_model=FileUploadResponse)
async def bulk_search_companies(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Массовый поиск информации о компаниях из файла"""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы Excel (.xlsx, .xls) и CSV")
    
    try:
        content = await file.read()
        
        # Определяем тип файла и читаем данные
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Предполагаем, что названия компаний в первом столбце
        company_names = df.iloc[:, 0].dropna().unique().tolist()
        
        companies_processed = 0
        companies_found = 0
        
        # Обрабатываем каждую компанию
        for company_name in company_names:
            if not company_name or len(str(company_name).strip()) == 0:
                continue
                
            company_name = str(company_name).strip()
            companies_processed += 1
            
            # Проверяем, есть ли уже такая компания в БД
            existing_company = db.query(Company).filter(Company.name == company_name).first()
            if existing_company:
                continue
            
            # Поиск информации через Polza.AI
            company_info = await polza_client.search_company_info(company_name)
            
            if company_info:
                companies_found += 1
                
                # Сохраняем в БД
                new_company = Company(
                    name=company_name,
                    website=company_info.get("website", ""),
                    email=company_info.get("email", ""),
                    address=company_info.get("address", ""),
                    phone=company_info.get("phone", ""),
                    description=company_info.get("description", ""),
                    equipment_purchased=company_info.get("equipment", "")
                )
                db.add(new_company)
        
        db.commit()
        
        return FileUploadResponse(
            message=f"Обработано {companies_processed} компаний, найдено информации для {companies_found}",
            companies_processed=companies_processed,
            companies_found=companies_found
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")

@app.get("/equipment", response_model=List[EquipmentSchema])
async def get_equipment(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всего оборудования"""
    equipment = db.query(Equipment).offset(skip).limit(limit).all()
    return equipment

@app.get("/search-logs")
async def get_search_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить историю поисков"""
    logs = db.query(SearchLog).order_by(SearchLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs

# ===== DIALOG ENDPOINTS =====

@app.post("/dialogs", response_model=Dialog)
async def create_dialog(dialog: DialogCreate, db: Session = Depends(get_db)):
    """Создать новый диалог"""
    from database import Dialog as DialogModel
    db_dialog = DialogModel(title=dialog.title)
    db.add(db_dialog)
    db.commit()
    db.refresh(db_dialog)
    return db_dialog

@app.get("/dialogs", response_model=List[Dialog])
async def get_dialogs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список диалогов"""
    from database import Dialog as DialogModel
    dialogs = db.query(DialogModel).filter(DialogModel.is_active == True).order_by(DialogModel.updated_at.desc()).offset(skip).limit(limit).all()
    return dialogs

@app.get("/dialogs/{dialog_id}", response_model=DialogWithMessages)
async def get_dialog(dialog_id: int, db: Session = Depends(get_db)):
    """Получить диалог с сообщениями"""
    from database import Dialog as DialogModel, DialogMessage as DialogMessageModel
    dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
    if not dialog:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    messages = db.query(DialogMessageModel).filter(DialogMessageModel.dialog_id == dialog_id).order_by(DialogMessageModel.created_at.asc()).all()
    dialog.messages = messages
    return dialog

@app.put("/dialogs/{dialog_id}", response_model=Dialog)
async def update_dialog(dialog_id: int, dialog_update: DialogUpdate, db: Session = Depends(get_db)):
    """Обновить диалог"""
    from database import Dialog as DialogModel
    dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
    if not dialog:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    if dialog_update.title is not None:
        dialog.title = dialog_update.title
    if dialog_update.is_active is not None:
        dialog.is_active = dialog_update.is_active
    
    dialog.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dialog)
    return dialog

@app.delete("/dialogs/{dialog_id}")
async def delete_dialog(dialog_id: int, db: Session = Depends(get_db)):
    """Удалить диалог (мягкое удаление)"""
    from database import Dialog as DialogModel
    dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
    if not dialog:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    dialog.is_active = False
    dialog.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Диалог удален"}

@app.post("/dialogs/{dialog_id}/messages", response_model=DialogMessage)
async def add_dialog_message(dialog_id: int, message: DialogMessageCreate, db: Session = Depends(get_db)):
    """Добавить сообщение в диалог"""
    from database import Dialog as DialogModel, DialogMessage as DialogMessageModel
    # Проверяем, что диалог существует
    dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
    if not dialog:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    db_message = DialogMessageModel(
        dialog_id=dialog_id,
        role=message.role,
        content=message.content
    )
    db.add(db_message)
    
    # Обновляем время последнего изменения диалога
    dialog.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)
    return db_message

# ===== DIALOG SETTINGS ENDPOINTS =====

@app.post("/dialogs/{dialog_id}/settings", response_model=DialogSettings)
async def create_dialog_settings(dialog_id: int, settings: DialogSettingsCreate, db: Session = Depends(get_db)):
    """Создать настройки для диалога"""
    from database import Dialog as DialogModel, DialogSettings as DialogSettingsModel
    
    # Проверяем, что диалог существует
    dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
    if not dialog:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    # Проверяем, есть ли уже настройки
    existing_settings = db.query(DialogSettingsModel).filter(DialogSettingsModel.dialog_id == dialog_id).first()
    if existing_settings:
        raise HTTPException(status_code=400, detail="Настройки для этого диалога уже существуют")
    
    db_settings = DialogSettingsModel(
        dialog_id=dialog_id,
        system_prompt=settings.system_prompt,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens
    )
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

@app.get("/dialogs/{dialog_id}/settings", response_model=DialogSettings)
async def get_dialog_settings(dialog_id: int, db: Session = Depends(get_db)):
    """Получить настройки диалога"""
    from database import DialogSettings as DialogSettingsModel
    
    settings = db.query(DialogSettingsModel).filter(DialogSettingsModel.dialog_id == dialog_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Настройки для диалога не найдены")
    return settings

@app.put("/dialogs/{dialog_id}/settings", response_model=DialogSettings)
async def update_dialog_settings(dialog_id: int, settings_update: DialogSettingsUpdate, db: Session = Depends(get_db)):
    """Обновить настройки диалога"""
    from database import DialogSettings as DialogSettingsModel
    
    settings = db.query(DialogSettingsModel).filter(DialogSettingsModel.dialog_id == dialog_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Настройки для диалога не найдены")
    
    if settings_update.system_prompt is not None:
        settings.system_prompt = settings_update.system_prompt
    if settings_update.model is not None:
        settings.model = settings_update.model
    if settings_update.temperature is not None:
        settings.temperature = settings_update.temperature
    if settings_update.max_tokens is not None:
        settings.max_tokens = settings_update.max_tokens
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings

# ===== ASSISTANT ENDPOINTS =====

@app.post("/assistants", response_model=Assistant)
async def create_assistant(assistant: AssistantCreate, db: Session = Depends(get_db)):
    """Создать нового помощника"""
    from database import Assistant as AssistantModel
    
    db_assistant = AssistantModel(
        name=assistant.name,
        description=assistant.description,
        system_prompt=assistant.system_prompt,
        model=assistant.model,
        temperature=assistant.temperature,
        max_tokens=assistant.max_tokens
    )
    db.add(db_assistant)
    db.commit()
    db.refresh(db_assistant)
    return db_assistant

@app.get("/assistants", response_model=List[Assistant])
async def get_assistants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список помощников"""
    from database import Assistant as AssistantModel
    
    assistants = db.query(AssistantModel).filter(AssistantModel.is_active == True).order_by(AssistantModel.created_at.desc()).offset(skip).limit(limit).all()
    return assistants

@app.get("/assistants/{assistant_id}", response_model=Assistant)
async def get_assistant(assistant_id: int, db: Session = Depends(get_db)):
    """Получить помощника по ID"""
    from database import Assistant as AssistantModel
    
    assistant = db.query(AssistantModel).filter(AssistantModel.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Помощник не найден")
    return assistant

@app.put("/assistants/{assistant_id}", response_model=Assistant)
async def update_assistant(assistant_id: int, assistant_update: AssistantUpdate, db: Session = Depends(get_db)):
    """Обновить помощника"""
    from database import Assistant as AssistantModel
    
    assistant = db.query(AssistantModel).filter(AssistantModel.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Помощник не найден")
    
    if assistant_update.name is not None:
        assistant.name = assistant_update.name
    if assistant_update.description is not None:
        assistant.description = assistant_update.description
    if assistant_update.system_prompt is not None:
        assistant.system_prompt = assistant_update.system_prompt
    if assistant_update.model is not None:
        assistant.model = assistant_update.model
    if assistant_update.temperature is not None:
        assistant.temperature = assistant_update.temperature
    if assistant_update.max_tokens is not None:
        assistant.max_tokens = assistant_update.max_tokens
    if assistant_update.is_active is not None:
        assistant.is_active = assistant_update.is_active
    
    assistant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant)
    return assistant

@app.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: int, db: Session = Depends(get_db)):
    """Удалить помощника (мягкое удаление)"""
    from database import Assistant as AssistantModel
    
    assistant = db.query(AssistantModel).filter(AssistantModel.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Помощник не найден")
    
    assistant.is_active = False
    assistant.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Помощник удален"}

# ===== FILE UPLOAD ENDPOINTS =====

@app.post("/dialogs/{dialog_id}/files", response_model=DialogFile)
async def upload_dialog_file(dialog_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Загрузить файл в диалог"""
    from database import Dialog as DialogModel, DialogFile as DialogFileModel
    import os
    import uuid
    
    # Проверяем, что диалог существует
    dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
    if not dialog:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    # Создаем директорию для файлов диалога
    upload_dir = f"uploads/dialogs/{dialog_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Определяем тип файла
    file_type = file.content_type or "application/octet-stream"
    
    # Читаем содержимое для текстовых файлов
    file_content = None
    if file_type.startswith("text/"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
        except:
            pass
    
    # Сохраняем информацию о файле в базу
    db_file = DialogFileModel(
        dialog_id=dialog_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file_type,
        content=file_content
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@app.get("/dialogs/{dialog_id}/files", response_model=List[DialogFile])
async def get_dialog_files(dialog_id: int, db: Session = Depends(get_db)):
    """Получить файлы диалога"""
    from database import DialogFile as DialogFileModel
    
    files = db.query(DialogFileModel).filter(DialogFileModel.dialog_id == dialog_id).order_by(DialogFileModel.created_at.desc()).all()
    return files

@app.delete("/dialogs/{dialog_id}/files/{file_id}")
async def delete_dialog_file(dialog_id: int, file_id: int, db: Session = Depends(get_db)):
    """Удалить файл диалога"""
    from database import DialogFile as DialogFileModel
    import os
    
    file = db.query(DialogFileModel).filter(DialogFileModel.id == file_id, DialogFileModel.dialog_id == dialog_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Удаляем файл с диска
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Удаляем запись из базы
    db.delete(file)
    db.commit()
    return {"message": "Файл удален"}

# ===== AVAILABLE MODELS ENDPOINT =====

@app.get("/models")
async def get_available_models():
    """Получить список доступных моделей"""
    # Список моделей с Polza.AI (обновляется по мере добавления новых)
    models = [
        {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "description": "Самая мощная модель OpenAI с отличным пониманием контекста",
            "max_tokens": 4096,
            "supports_vision": True
        },
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4o Mini",
            "description": "Быстрая и эффективная модель для большинства задач",
            "max_tokens": 4096,
            "supports_vision": True
        },
        {
            "id": "claude-3-5-sonnet-20241022",
            "name": "Claude 3.5 Sonnet",
            "description": "Продвинутая модель Anthropic с отличными аналитическими способностями",
            "max_tokens": 4096,
            "supports_vision": True
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "name": "Claude 3.5 Haiku",
            "description": "Быстрая модель Claude для простых задач",
            "max_tokens": 4096,
            "supports_vision": True
        },
        {
            "id": "gemini-1.5-pro",
            "name": "Gemini 1.5 Pro",
            "description": "Мощная модель Google с поддержкой больших контекстов",
            "max_tokens": 8192,
            "supports_vision": True
        },
        {
            "id": "gemini-1.5-flash",
            "name": "Gemini 1.5 Flash",
            "description": "Быстрая модель Gemini для повседневных задач",
            "max_tokens": 8192,
            "supports_vision": True
        }
    ]
    return models

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(chat_request: ChatRequest):
    """Общение с AI в режиме чата (legacy endpoint)"""
    try:
        # Получаем текущую историю разговора
        conversation_history = chat_request.conversation_history.copy() if chat_request.conversation_history else []
        
        # Проверяем, нужно ли создать резюме (если больше 20 сообщений)
        if len(conversation_history) >= 20:
            print(f"История диалога содержит {len(conversation_history)} сообщений, создаем резюме...")
            
            # Создаем резюме первых 18 сообщений (оставляем последние 2)
            messages_to_summarize = conversation_history[:-2]
            summary = await polza_client.summarize_conversation(messages_to_summarize)
            
            # Заменяем старую историю на резюме + последние 2 сообщения
            conversation_history = [
                ChatMessage(
                    role="system",
                    content=f"Резюме предыдущего диалога: {summary}",
                    timestamp=datetime.utcnow()
                )
            ] + conversation_history[-2:]
            
            print(f"История сокращена до {len(conversation_history)} сообщений")
        
        # Получаем ответ от AI с обновленной историей
        ai_response = await polza_client.chat_with_llm(
            chat_request.message, 
            conversation_history
        )
        
        # Добавляем сообщение пользователя
        conversation_history.append(ChatMessage(
            role="user",
            content=chat_request.message,
            timestamp=datetime.utcnow()
        ))
        
        # Добавляем ответ AI
        conversation_history.append(ChatMessage(
            role="assistant",
            content=ai_response,
            timestamp=datetime.utcnow()
        ))
        
        return ChatResponse(
            message=ai_response,
            conversation_history=conversation_history
        )
        
    except Exception as e:
        print(f"Ошибка в чате: {e}")
        error_message = "Извините, произошла ошибка при обработке вашего сообщения."
        
        # Возвращаем ошибку с историей
        conversation_history = chat_request.conversation_history.copy() if chat_request.conversation_history else []
        conversation_history.append(ChatMessage(
            role="user",
            content=chat_request.message,
            timestamp=datetime.utcnow()
        ))
        conversation_history.append(ChatMessage(
            role="assistant",
            content=error_message,
            timestamp=datetime.utcnow()
        ))
        
        return ChatResponse(
            message=error_message,
            conversation_history=conversation_history
        )

@app.post("/chat/dialog", response_model=ChatResponseWithDialog)
async def chat_with_dialog(chat_request: ChatRequestWithDialog, db: Session = Depends(get_db)):
    """Общение с AI с сохранением в диалог"""
    try:
        from database import Dialog as DialogModel, DialogMessage as DialogMessageModel
        
        # Если dialog_id не указан, создаем новый диалог
        if not chat_request.dialog_id:
            # Создаем заголовок на основе первого сообщения
            title = chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message
            dialog = DialogModel(title=title)
            db.add(dialog)
            db.commit()
            db.refresh(dialog)
            dialog_id = dialog.id
        else:
            dialog_id = chat_request.dialog_id
            # Проверяем, что диалог существует
            dialog = db.query(DialogModel).filter(DialogModel.id == dialog_id).first()
            if not dialog:
                raise HTTPException(status_code=404, detail="Диалог не найден")
        
        # Получаем историю сообщений из базы данных
        db_messages = db.query(DialogMessageModel).filter(DialogMessageModel.dialog_id == dialog_id).order_by(DialogMessageModel.created_at.asc()).all()
        
        # Конвертируем в формат для AI
        conversation_history = []
        for msg in db_messages:
            conversation_history.append(ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at
            ))
        
        # Проверяем, нужно ли создать резюме (если больше 20 сообщений)
        if len(conversation_history) >= 20:
            print(f"История диалога содержит {len(conversation_history)} сообщений, создаем резюме...")
            
            # Создаем резюме первых 18 сообщений (оставляем последние 2)
            messages_to_summarize = conversation_history[:-2]
            summary = await polza_client.summarize_conversation(messages_to_summarize)
            
            # Удаляем старые сообщения из базы (кроме последних 2)
            messages_to_delete = db_messages[:-2]
            for msg in messages_to_delete:
                db.delete(msg)
            
            # Добавляем резюме как системное сообщение
            summary_message = DialogMessageModel(
                dialog_id=dialog_id,
                role="system",
                content=f"Резюме предыдущего диалога: {summary}"
            )
            db.add(summary_message)
            
            # Обновляем conversation_history
            conversation_history = [
                ChatMessage(
                    role="system",
                    content=f"Резюме предыдущего диалога: {summary}",
                    timestamp=datetime.utcnow()
                )
            ] + conversation_history[-2:]
            
            print(f"История сокращена до {len(conversation_history)} сообщений")
        
        # Получаем настройки диалога
        dialog_settings = None
        try:
            from database import DialogSettings as DialogSettingsModel
            settings = db.query(DialogSettingsModel).filter(DialogSettingsModel.dialog_id == dialog_id).first()
            if settings:
                dialog_settings = {
                    'system_prompt': settings.system_prompt,
                    'model': settings.model,
                    'temperature': settings.temperature,
                    'max_tokens': settings.max_tokens
                }
        except Exception as e:
            print(f"Ошибка при загрузке настроек диалога: {e}")
        
        # Получаем ответ от AI
        ai_response = await polza_client.chat_with_llm(
            chat_request.message, 
            conversation_history,
            dialog_settings
        )
        
        # Сохраняем сообщение пользователя в базу
        user_message = DialogMessageModel(
            dialog_id=dialog_id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        
        # Сохраняем ответ AI в базу
        ai_message = DialogMessageModel(
            dialog_id=dialog_id,
            role="assistant",
            content=ai_response
        )
        db.add(ai_message)
        
        # Обновляем время последнего изменения диалога
        dialog.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Формируем ответ
        conversation_history.append(ChatMessage(
            role="user",
            content=chat_request.message,
            timestamp=datetime.utcnow()
        ))
        conversation_history.append(ChatMessage(
            role="assistant",
            content=ai_response,
            timestamp=datetime.utcnow()
        ))
        
        return ChatResponseWithDialog(
            message=ai_response,
            conversation_history=conversation_history,
            dialog_id=dialog_id
        )
        
    except Exception as e:
        print(f"Ошибка в чате с диалогом: {e}")
        error_message = "Извините, произошла ошибка при обработке вашего сообщения."
        
        # Возвращаем ошибку
        conversation_history = chat_request.conversation_history.copy() if chat_request.conversation_history else []
        conversation_history.append(ChatMessage(
            role="user",
            content=chat_request.message,
            timestamp=datetime.utcnow()
        ))
        conversation_history.append(ChatMessage(
            role="assistant",
            content=error_message,
            timestamp=datetime.utcnow()
        ))
        
        return ChatResponseWithDialog(
            message=error_message,
            conversation_history=conversation_history,
            dialog_id=chat_request.dialog_id or 0
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
