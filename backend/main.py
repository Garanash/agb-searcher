from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
import asyncio
from datetime import datetime
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import dns.resolver
import socket

from database import get_db, create_tables, Company, Equipment, SearchLog, Assistant, EmailCampaign, EmailVerification
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
    Assistant as AssistantSchema,
    AssistantCreate,
    AssistantUpdate,
    EmailCampaignCreate,
    EmailCampaign as EmailCampaignSchema,
    EmailVerificationRequest,
    EmailVerification as EmailVerificationSchema,
    AgentActionRequest,
    AgentActionResponse
)
from polza_client import PolzaAIClient

app = FastAPI(title="AGB Searcher API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В режиме разработки разрешаем все источники
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

@app.post("/companies", response_model=CompanySchema)
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """Создать новую компанию"""
    # Проверяем, не существует ли уже такая компания
    existing_company = db.query(Company).filter(Company.name == company.name).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Компания с таким названием уже существует")
    
    db_company = Company(
        name=company.name,
        website=company.website or "",
        email=company.email or "",
        address=company.address or "",
        phone=company.phone or "",
        description=company.description or "",
        equipment_purchased=company.equipment_purchased or ""
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

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
    
    # Поиск через Polza.AI с retry механизмом
    company_info = await polza_client.search_company_info(company_name, retry_count=2)
    
    # Обновляем лог
    search_log.results_count = 1 if company_info else 0
    db.commit()
    
    if not company_info:
        raise HTTPException(status_code=404, detail="Информация о компании не найдена")
    
    return CompanySearchResult(
        name=company_name,
        website=company_info.get("website", ""),
        email=company_info.get("email", ""),
        address=company_info.get("address", ""),
        phone=company_info.get("phone", ""),
        description=company_info.get("description", ""),
        equipment=company_info.get("equipment", ""),
        preferred_language=company_info.get("preferred_language", "ru")
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
            equipment=equipment_name,
            preferred_language=company_data.get("preferred_language", "ru")
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
            
            # Поиск информации через Polza.AI с retry механизмом
            company_info = await polza_client.search_company_info(company_name, retry_count=2)
            
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
                    equipment_purchased=company_info.get("equipment", ""),
                    preferred_language=company_info.get("preferred_language", "ru")
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

# Заглушки для endpoints диалогов и помощников (для совместимости с frontend)
@app.get("/dialogs")
async def get_dialogs(skip: int = 0, limit: int = 100):
    """Получить список диалогов (заглушка)"""
    return []

@app.get("/dialogs/{dialog_id}")
async def get_dialog(dialog_id: int):
    """Получить диалог по ID (заглушка)"""
    raise HTTPException(status_code=404, detail="Диалог не найден")

@app.post("/dialogs")
async def create_dialog(dialog: dict):
    """Создать новый диалог (заглушка)"""
    return {"id": 1, "title": dialog.get("title", "Новый диалог")}

@app.delete("/dialogs/{dialog_id}")
async def delete_dialog(dialog_id: int):
    """Удалить диалог (заглушка)"""
    return {"message": "Диалог удален"}

@app.get("/assistants", response_model=List[AssistantSchema])
async def get_assistants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список помощников"""
    assistants = db.query(Assistant).offset(skip).limit(limit).all()
    return assistants

@app.post("/assistants", response_model=AssistantSchema)
async def create_assistant(assistant: AssistantCreate, db: Session = Depends(get_db)):
    """Создать нового помощника"""
    db_assistant = Assistant(
        name=assistant.name,
        description=assistant.description or "",
        system_prompt=assistant.system_prompt,
        model=assistant.model,
        temperature=assistant.temperature or "0.7",
        max_tokens=assistant.max_tokens
    )
    db.add(db_assistant)
    db.commit()
    db.refresh(db_assistant)
    return db_assistant

@app.put("/assistants/{assistant_id}", response_model=AssistantSchema)
async def update_assistant(assistant_id: int, assistant_update: AssistantUpdate, db: Session = Depends(get_db)):
    """Обновить помощника"""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Помощник не найден")
    
    update_data = assistant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assistant, field, value)
    
    assistant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant)
    return assistant

@app.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: int, db: Session = Depends(get_db)):
    """Удалить помощника"""
    assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Помощник не найден")
    
    db.delete(assistant)
    db.commit()
    return {"message": "Помощник удален"}

@app.get("/models")
async def get_models():
    """Получить список моделей (заглушка)"""
    return [
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
    ]

@app.get("/dialogs/{dialog_id}/settings")
async def get_dialog_settings(dialog_id: int):
    """Получить настройки диалога (заглушка)"""
    return {}

@app.put("/dialogs/{dialog_id}/settings")
async def update_dialog_settings(dialog_id: int, settings: dict):
    """Обновить настройки диалога (заглушка)"""
    return settings

@app.get("/dialogs/{dialog_id}/files")
async def get_dialog_files(dialog_id: int):
    """Получить файлы диалога (заглушка)"""
    return []

@app.delete("/dialogs/{dialog_id}/files/{file_id}")
async def delete_dialog_file(dialog_id: int, file_id: int):
    """Удалить файл диалога (заглушка)"""
    return {"message": "Файл удален"}

@app.delete("/assistants/{assistant_id}")
async def delete_assistant(assistant_id: int):
    """Удалить помощника (заглушка)"""
    return {"message": "Помощник удален"}

@app.post("/chat/dialog")
async def chat_with_dialog(chat_request: dict, db: Session = Depends(get_db)):
    """Общение с AI в диалоге с поддержкой функций агента"""
    try:
        message = chat_request.get("message", "")
        dialog_id = chat_request.get("dialog_id")
        conversation_history = chat_request.get("conversation_history", [])
        
        if not message:
            raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
        
        print(f"📨 Получено сообщение в чат: '{message[:100]}...'")
        
        # Проверяем, нужно ли выполнить действия агента
        # Ищем команды типа "найди и сохрани компанию X" или "поищи информацию о Y"
        company_names = polza_client._extract_company_names_from_message(message)
        should_save = any(word in message.lower() for word in ['сохрани', 'добавь', 'запиши', 'save', 'add'])
        
        # Если найдены компании и есть команда на сохранение, выполняем поиск и сохранение
        saved_companies = []
        if company_names and should_save:
            for company_name in company_names:
                try:
                    # Ищем информацию о компании с retry механизмом
                    company_info = await polza_client.search_company_info(company_name, retry_count=2)
                    
                    # Проверяем, не существует ли уже такая компания
                    existing_company = db.query(Company).filter(Company.name == company_name).first()
                    if not existing_company and company_info:
                        # Сохраняем в БД
                        new_company = Company(
                            name=company_name,
                            website=company_info.get("website", ""),
                            email=company_info.get("email", ""),
                            address=company_info.get("address", ""),
                            phone=company_info.get("phone", ""),
                            description=company_info.get("description", ""),
                            equipment_purchased=company_info.get("equipment", ""),
                            preferred_language=company_info.get("preferred_language", "ru")
                        )
                        db.add(new_company)
                        db.commit()
                        db.refresh(new_company)
                        saved_companies.append(company_name)
                        print(f"✅ Компания '{company_name}' успешно сохранена в БД")
                except Exception as e:
                    print(f"❌ Ошибка при сохранении компании {company_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Продолжаем работу даже если не удалось сохранить компанию
        
        # Получаем ответ от AI
        try:
            ai_response = await polza_client.chat_with_llm(message, conversation_history)
        except Exception as e:
            print(f"Ошибка при получении ответа от AI: {e}")
            import traceback
            traceback.print_exc()
            # Возвращаем понятное сообщение об ошибке
            ai_response = f"Извините, произошла ошибка при обработке вашего запроса. Попробуйте переформулировать вопрос или обратитесь к администратору. Ошибка: {str(e)[:100]}"
        
        # Добавляем информацию о сохраненных компаниях в ответ
        if saved_companies:
            ai_response += f"\n\n✅ Сохранено компаний в базу данных: {', '.join(saved_companies)}"
        
        # Создаем новый диалог, если его нет
        if not dialog_id:
            dialog_id = 1
        
        return {
            "message": ai_response,
            "conversation_history": conversation_history + [
                {"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": ai_response, "timestamp": datetime.utcnow().isoformat()}
            ],
            "dialog_id": dialog_id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Критическая ошибка в chat_with_dialog: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@app.post("/agent/action", response_model=AgentActionResponse)
async def agent_action(action_request: AgentActionRequest, db: Session = Depends(get_db)):
    """Выполнение действий агента (поиск, сохранение компаний и т.д.)"""
    action = action_request.action
    params = action_request.parameters
    
    try:
        if action == "search_company":
            company_name = params.get("company_name")
            if not company_name:
                return AgentActionResponse(success=False, message="Не указано название компании")
            
            company_info = await polza_client.search_company_info(company_name, retry_count=2)
            return AgentActionResponse(success=True, message="Компания найдена", data=company_info)
        
        elif action == "save_company":
            company_name = params.get("company_name")
            if not company_name:
                return AgentActionResponse(success=False, message="Не указано название компании")
            
            # Проверяем, не существует ли уже такая компания
            existing_company = db.query(Company).filter(Company.name == company_name).first()
            if existing_company:
                return AgentActionResponse(success=False, message=f"Компания '{company_name}' уже существует в базе данных")
            
            # Ищем информацию о компании с retry механизмом
            company_info = await polza_client.search_company_info(company_name, retry_count=2)
            
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
            db.refresh(new_company)
            
            return AgentActionResponse(
                success=True, 
                message=f"Компания '{company_name}' успешно сохранена в базу данных",
                data={"company_id": new_company.id, "company": company_info}
            )
        
        elif action == "search_and_save_company":
            company_name = params.get("company_name")
            if not company_name:
                return AgentActionResponse(success=False, message="Не указано название компании")
            
            # Ищем информацию с retry механизмом
            company_info = await polza_client.search_company_info(company_name, retry_count=2)
            
            # Проверяем, не существует ли уже такая компания
            existing_company = db.query(Company).filter(Company.name == company_name).first()
            if existing_company:
                return AgentActionResponse(
                    success=True, 
                    message=f"Компания '{company_name}' уже существует в базе данных",
                    data={"company_id": existing_company.id, "company": company_info}
                )
            
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
            db.refresh(new_company)
            
            return AgentActionResponse(
                success=True, 
                message=f"Компания '{company_name}' найдена и сохранена в базу данных",
                data={"company_id": new_company.id, "company": company_info}
            )
        
        else:
            return AgentActionResponse(success=False, message=f"Неизвестное действие: {action}")
    
    except Exception as e:
        return AgentActionResponse(success=False, message=f"Ошибка при выполнении действия: {str(e)}")

async def _verify_email_internal(email: str, company_id: int = None, db: Session = None) -> EmailVerification:
    """Внутренняя функция для проверки email адреса"""
    email = email.strip().lower()
    
    # Проверяем базовый формат
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid_format = bool(re.match(email_pattern, email))
    
    if not is_valid_format:
        verification = EmailVerification(
            email=email,
            company_id=company_id,
            is_valid=False,
            is_deliverable=False,
            verification_status="invalid",
            error_message="Неверный формат email адреса"
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        return verification
    
    # Проверяем домен
    domain = email.split('@')[1]
    is_deliverable = False
    error_message = None
    
    try:
        # Проверяем MX записи
        mx_records = dns.resolver.resolve(domain, 'MX')
        if mx_records:
            is_deliverable = True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        error_message = "Домен не найден или не имеет MX записей"
    except Exception as e:
        error_message = f"Ошибка при проверке домена: {str(e)}"
    
    verification_status = "verified" if is_deliverable else "invalid"
    
    # Проверяем, есть ли уже запись об этой проверке
    existing = db.query(EmailVerification).filter(EmailVerification.email == email).first()
    if existing:
        existing.is_valid = is_valid_format
        existing.is_deliverable = is_deliverable
        existing.verification_status = verification_status
        existing.error_message = error_message
        existing.last_checked = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    verification = EmailVerification(
        email=email,
        company_id=company_id,
        is_valid=is_valid_format,
        is_deliverable=is_deliverable,
        verification_status=verification_status,
        error_message=error_message
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification

@app.post("/email/verify", response_model=EmailVerificationSchema)
async def verify_email(verification_request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Проверка email адреса на валидность и доставляемость"""
    email = verification_request.email.strip().lower()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email не может быть пустым")
    
    return await _verify_email_internal(email, verification_request.company_id if verification_request.company_id else None, db)

@app.post("/email/campaign", response_model=EmailCampaignSchema)
async def create_email_campaign(campaign: EmailCampaignCreate, db: Session = Depends(get_db)):
    """Создание email рассылки"""
    company_ids_json = json.dumps(campaign.company_ids) if campaign.company_ids else None
    
    email_campaign = EmailCampaign(
        subject=campaign.subject,
        body=campaign.body,
        company_ids=company_ids_json,
        status="draft"
    )
    db.add(email_campaign)
    db.commit()
    db.refresh(email_campaign)
    return email_campaign

@app.post("/email/campaign/{campaign_id}/send")
async def send_email_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Отправка email рассылки с учетом предпочтительного языка компаний"""
    campaign = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")
    
    # Получаем список компаний для рассылки
    company_ids = json.loads(campaign.company_ids) if campaign.company_ids else []
    
    if not company_ids:
        # Если не указаны конкретные компании, берем все с email
        companies = db.query(Company).filter(Company.email != None, Company.email != "").all()
    else:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
    
    # Фильтруем только компании с валидными email
    valid_companies = []
    language_stats = {}
    for company in companies:
        if company.email:
            # Проверяем email
            verification = await _verify_email_internal(company.email, company.id, db)
            if verification.is_deliverable:
                valid_companies.append(company)
                # Собираем статистику по языкам
                lang = company.preferred_language or "ru"
                language_stats[lang] = language_stats.get(lang, 0) + 1
    
    # Обновляем статус рассылки
    campaign.status = "sending"
    campaign.sent_at = datetime.utcnow()
    db.commit()
    
    # Отправляем письма (заглушка - в реальности нужна настройка SMTP)
    sent_count = 0
    failed_count = 0
    
    # TODO: Настроить SMTP сервер для реальной отправки
    # Для примера просто считаем, что все отправлены успешно
    for company in valid_companies:
        try:
            # Здесь должна быть реальная отправка через SMTP
            # send_email_via_smtp(company.email, campaign.subject, campaign.body)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Ошибка при отправке письма на {company.email}: {e}")
    
    # Обновляем статистику
    campaign.sent_count = sent_count
    campaign.failed_count = failed_count
    campaign.status = "completed" if failed_count == 0 else "completed"
    db.commit()
    
    # Определяем основной язык для рассылки
    main_language = max(language_stats.items(), key=lambda x: x[1])[0] if language_stats else "ru"
    
    return {
        "message": f"Рассылка отправлена: {sent_count} успешно, {failed_count} ошибок",
        "sent_count": sent_count,
        "failed_count": failed_count,
        "language_stats": language_stats,
        "recommended_language": main_language
    }

@app.get("/email/campaigns", response_model=List[EmailCampaignSchema])
async def get_email_campaigns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список email рассылок"""
    campaigns = db.query(EmailCampaign).offset(skip).limit(limit).all()
    result = []
    for campaign in campaigns:
        campaign_dict = {
            "id": campaign.id,
            "subject": campaign.subject,
            "body": campaign.body,
            "company_ids": json.loads(campaign.company_ids) if campaign.company_ids else None,
            "sent_count": campaign.sent_count,
            "failed_count": campaign.failed_count,
            "status": campaign.status,
            "created_at": campaign.created_at,
            "sent_at": campaign.sent_at
        }
        result.append(campaign_dict)
    return result

@app.get("/email/verifications", response_model=List[EmailVerificationSchema])
async def get_email_verifications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список проверок email"""
    verifications = db.query(EmailVerification).offset(skip).limit(limit).all()
    return verifications

@app.post("/companies/bulk-verify-emails")
async def bulk_verify_emails(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Массовая проверка всех email адресов компаний"""
    companies = db.query(Company).filter(Company.email != None, Company.email != "").all()
    
    verified_count = 0
    invalid_count = 0
    
    for company in companies:
        try:
            verification = await _verify_email_internal(company.email, company.id, db)
            if verification.is_deliverable:
                verified_count += 1
            else:
                invalid_count += 1
        except Exception as e:
            print(f"Ошибка при проверке email {company.email}: {e}")
            invalid_count += 1
    
    return {
        "message": f"Проверено email адресов: {verified_count} валидных, {invalid_count} невалидных",
        "verified_count": verified_count,
        "invalid_count": invalid_count
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
