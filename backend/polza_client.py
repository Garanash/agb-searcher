import httpx
import os
from typing import Dict, Any, List
import json

class PolzaAIClient:
    def __init__(self):
        self.api_key = os.getenv("POLZA_API_KEY", "ak_FojEdiuKBZJwcAdyGQiPUIKt2DDFsTlawov98zr6Npg")
        self.base_url = "https://api.polza.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, prompt: str, max_tokens: int = 2000) -> str:
        """Универсальный метод для отправки запросов к Polza.AI"""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"Отправляем запрос к Polza.AI: {prompt[:100]}...")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"Получен ответ от Polza.AI: {content[:100]}...")
                return content
                
            except httpx.HTTPError as e:
                print(f"Ошибка HTTP запроса к Polza.AI: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Статус код: {e.response.status_code}")
                    print(f"Ответ: {e.response.text}")
                raise e
            except Exception as e:
                print(f"Ошибка при обращении к Polza.AI: {e}")
                raise e
    
    def _validate_company_data(self, data: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """Валидация данных компании - проверяем, что данные выглядят реально"""
        validated = {
            "website": "",
            "email": "",
            "address": "",
            "phone": "",
            "description": "",
            "equipment": ""
        }
        
        # Проверяем website
        website = data.get("website", "").strip()
        if website and website.startswith("http") and "." in website:
            validated["website"] = website
        
        # Проверяем email
        email = data.get("email", "").strip()
        if email and "@" in email and "." in email.split("@")[1]:
            validated["email"] = email
        
        # Проверяем адрес - должен содержать реальные элементы
        address = data.get("address", "").strip()
        if address and any(word in address.lower() for word in ["г.", "ул.", "д.", "мск", "спб", "москва", "санкт"]):
            validated["address"] = address
        
        # Проверяем телефон - должен содержать цифры и выглядеть как телефон
        phone = data.get("phone", "").strip()
        if phone and any(char.isdigit() for char in phone) and len(phone) > 7:
            validated["phone"] = phone
        
        # Описание и оборудование - оставляем как есть, если не пустые
        description = data.get("description", "").strip()
        if description:
            validated["description"] = description
            
        equipment = data.get("equipment", "").strip()
        if equipment:
            validated["equipment"] = equipment
        
        print(f"Валидация данных для {company_name}: {validated}")
        return validated
    
    async def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """Поиск информации о компании через Polza.AI"""
        
        prompt = f"""
        Найди ТОЛЬКО РЕАЛЬНУЮ и ПРОВЕРЕННУЮ информацию о компании "{company_name}" в России.
        
        ВАЖНО: НЕ ВЫДУМЫВАЙ данные! Если информации нет - оставь поле пустым.
        
        Ищи только:
        - Официальный сайт компании (только реальный, проверенный)
        - Контактные email адреса (только с официальных сайтов)
        - Физический адрес (только из официальных источников)
        - Телефон (только из официальных источников)
        - Краткое описание деятельности (только факты)
        - Оборудование (только если есть публичная информация)
        
        Если какой-то информации нет в открытых источниках - оставь поле пустым "".
        
        Ответь ТОЛЬКО в формате JSON без дополнительного текста:
        {{
            "website": "https://real-website.com",
            "email": "real@email.com",
            "address": "реальный адрес",
            "phone": "реальный телефон",
            "description": "реальное описание",
            "equipment": "реальное оборудование"
        }}
        """
        
        try:
            content = await self._make_request(prompt, max_tokens=2000)
            
            # Пытаемся извлечь JSON из ответа
            try:
                # Ищем JSON в ответе
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Валидация: проверяем, что данные выглядят реально
                    validated_result = self._validate_company_data(result, company_name)
                    print(f"Успешно распарсили и валидировали JSON для компании {company_name}")
                    return validated_result
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                print(f"Содержимое ответа: {content}")
            
            # Если не удалось распарсить JSON, возвращаем пустые поля
            return {
                "website": "",
                "email": "",
                "address": "",
                "phone": "",
                "description": "",
                "equipment": ""
            }
                
        except Exception as e:
            print(f"Ошибка при поиске информации о компании {company_name}: {e}")
            return {}
    
    async def search_companies_by_equipment(self, equipment_name: str) -> List[Dict[str, Any]]:
        """Поиск компаний, которые купили определенное оборудование"""
        
        prompt = f"""
        Найди РЕАЛЬНЫЕ компании в России, которые покупали или используют оборудование "{equipment_name}".
        
        ВАЖНО: НЕ ВЫДУМЫВАЙ данные! Ищи только в открытых источниках.
        
        Для каждой компании найди ТОЛЬКО ПРОВЕРЕННУЮ информацию:
        - Название компании (реальное)
        - Официальный сайт (только если есть)
        - Контактный email (только с официальных сайтов)
        - Адрес (только из официальных источников)
        - Телефон (только из официальных источников)
        - Краткое описание (только факты)
        
        Если какой-то информации нет - оставь поле пустым "".
        Если компаний не найдено - верни пустой массив [].
        
        Ответь ТОЛЬКО в формате JSON массива без дополнительного текста:
        [
            {{
                "name": "Реальное название компании",
                "website": "https://real-website.com",
                "email": "real@email.com",
                "address": "реальный адрес",
                "phone": "реальный телефон",
                "description": "реальное описание"
            }}
        ]
        """
        
        try:
            content = await self._make_request(prompt, max_tokens=4000)
            
            # Пытаемся извлечь JSON массив из ответа
            try:
                # Ищем JSON массив в ответе
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Валидация каждой компании в списке
                    validated_companies = []
                    for company in result:
                        if isinstance(company, dict):
                            validated_company = self._validate_company_data(company, company.get("name", "Unknown"))
                            # Проверяем, что у компании есть хотя бы название
                            if validated_company.get("name") or company.get("name"):
                                validated_company["name"] = company.get("name", "")
                                validated_companies.append(validated_company)
                    
                    print(f"Успешно распарсили и валидировали {len(validated_companies)} компаний для оборудования {equipment_name}")
                    return validated_companies
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                print(f"Содержимое ответа: {content}")
            
            # Если не удалось распарсить JSON, возвращаем пустой список
            return []
            
        except Exception as e:
            print(f"Ошибка при поиске компаний по оборудованию {equipment_name}: {e}")
            return []
    
    async def chat_with_llm(self, message: str, conversation_history: List[Dict[str, Any]] = None, custom_settings: Dict[str, Any] = None) -> str:
        """Общение с LLM в режиме чата"""
        
        # Формируем контекст для чата
        system_prompt = """Ты - помощник по поиску информации о компаниях и оборудовании. 
        Ты помогаешь пользователям находить информацию о российских компаниях, их контактах, 
        оборудовании и деятельности. Отвечай на русском языке, будь полезным и информативным.
        Если пользователь спрашивает о компаниях или оборудовании, предложи использовать 
        функции поиска в системе.
        
        **ВАЖНО**: Всегда форматируй свои ответы в Markdown для лучшей читаемости:
        - Используй заголовки (# ## ###) для структурирования
        - Используй списки (- или 1.) для перечислений
        - Выделяй важные моменты **жирным** или *курсивом*
        - Используй `код` для технических терминов
        - Создавай таблицы для структурированных данных
        - Используй > для цитат и важных замечаний"""
        
        # Если переданы кастомные настройки, используем их
        if custom_settings and custom_settings.get('system_prompt'):
            system_prompt = custom_settings['system_prompt']
        
        # Подготавливаем сообщения для API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем историю разговора
        if conversation_history:
            for msg in conversation_history:
                # Проверяем, это словарь или объект ChatMessage
                if hasattr(msg, 'role'):
                    # Это объект ChatMessage
                    role = msg.role
                    content = msg.content
                else:
                    # Это словарь
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                
                # Если это системное сообщение с резюме, добавляем его как системное
                if role == "system":
                    messages.append({"role": "system", "content": content})
                else:
                    messages.append({"role": role, "content": content})
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": message})
        
        # Используем кастомные настройки или значения по умолчанию
        model = custom_settings.get('model', 'gpt-4o') if custom_settings else 'gpt-4o'
        max_tokens = custom_settings.get('max_tokens', 1000) if custom_settings else 1000
        temperature = float(custom_settings.get('temperature', 0.7)) if custom_settings else 0.7
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"Отправляем сообщение в чат: {message[:50]}...")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"Получен ответ от LLM: {content[:50]}...")
                return content
                
            except httpx.HTTPError as e:
                print(f"Ошибка HTTP запроса к Polza.AI для чата: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Статус код: {e.response.status_code}")
                    print(f"Ответ: {e.response.text}")
                return "Извините, произошла ошибка при обращении к AI. Попробуйте позже."
            except Exception as e:
                print(f"Ошибка при общении с LLM: {e}")
                return "Извините, произошла ошибка при общении с AI. Попробуйте позже."
    
    async def summarize_conversation(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Создает краткое резюме диалога для сохранения контекста"""
        
        # Формируем текст диалога для сумаризации
        conversation_text = ""
        for msg in conversation_history:
            # Проверяем, это словарь или объект ChatMessage
            if hasattr(msg, 'role'):
                # Это объект ChatMessage
                role = msg.role
                content = msg.content
            else:
                # Это словарь
                role = msg.get("role", "user")
                content = msg.get("content", "")
            
            role_display = "Пользователь" if role == "user" else "AI"
            conversation_text += f"{role_display}: {content}\n"
        
        system_prompt = """Ты - помощник для создания краткого резюме диалога. 
        Создай краткое резюме (не более 200 слов) основного содержания диалога между пользователем и AI помощником.
        Сохрани ключевые темы, вопросы пользователя и важные ответы AI.
        Резюме должно быть на русском языке и помогать продолжить диалог с сохранением контекста."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Создай резюме этого диалога:\n\n{conversation_text}"}
        ]
        
        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print("Создаем резюме диалога...")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                summary = result["choices"][0]["message"]["content"]
                print(f"Создано резюме: {summary[:100]}...")
                return summary
                
            except Exception as e:
                print(f"Ошибка при создании резюме: {e}")
                return "Резюме диалога недоступно."
