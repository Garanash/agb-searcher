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
    
    async def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """Поиск информации о компании через Perplexity DeepSearch"""
        prompt = f"""
        Найди подробную информацию о компании "{company_name}":
        - Официальный сайт компании
        - Контактные email адреса
        - Физический адрес
        - Телефон
        - Краткое описание деятельности компании
        - Какое оборудование они могли покупать
        
        Ответь в формате JSON:
        {{
            "website": "https://example.com",
            "email": "info@example.com",
            "address": "г. Москва, ул. Примерная, д. 1",
            "phone": "+7 (495) 123-45-67",
            "description": "Описание деятельности",
            "equipment": "Список оборудования"
        }}
        """
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Пытаемся извлечь JSON из ответа
                try:
                    # Ищем JSON в ответе
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = content[start_idx:end_idx]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
                
                # Если не удалось распарсить JSON, возвращаем текстовый ответ
                return {
                    "website": "",
                    "email": "",
                    "address": "",
                    "phone": "",
                    "description": content,
                    "equipment": ""
                }
                
            except httpx.HTTPError as e:
                print(f"Ошибка HTTP запроса: {e}")
                return {}
            except Exception as e:
                print(f"Ошибка при поиске информации о компании: {e}")
                return {}
    
    async def search_companies_by_equipment(self, equipment_name: str) -> List[Dict[str, Any]]:
        """Поиск компаний, которые купили определенное оборудование"""
        prompt = f"""
        Найди компании в России, которые покупали или используют оборудование "{equipment_name}".
        
        Для каждой компании найди:
        - Название компании
        - Официальный сайт
        - Контактный email
        - Адрес
        - Телефон
        - Краткое описание
        
        Ответь в формате JSON массива:
        [
            {{
                "name": "Название компании",
                "website": "https://example.com",
                "email": "info@example.com",
                "address": "г. Москва, ул. Примерная, д. 1",
                "phone": "+7 (495) 123-45-67",
                "description": "Описание деятельности"
            }}
        ]
        
        Найди минимум 5-10 компаний.
        """
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Пытаемся извлечь JSON из ответа
                try:
                    # Ищем JSON массив в ответе
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = content[start_idx:end_idx]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
                
                # Если не удалось распарсить JSON, возвращаем пустой список
                return []
                
            except httpx.HTTPError as e:
                print(f"Ошибка HTTP запроса: {e}")
                return []
            except Exception as e:
                print(f"Ошибка при поиске компаний: {e}")
                return []
