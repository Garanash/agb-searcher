from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
import asyncio
from datetime import datetime

from database import get_db, create_tables, Company, Equipment, SearchLog
from schemas import (
    Company as CompanySchema, 
    CompanyCreate, 
    CompanyUpdate,
    Equipment as EquipmentSchema,
    EquipmentCreate,
    SearchRequest,
    CompanySearchResult,
    EquipmentSearchResult,
    FileUploadResponse
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
        raise HTTPException(status_code=404, detail="Информация о компании не найдена")
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
