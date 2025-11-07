import httpx
import os
from typing import Dict, Any, List
import json
import re
import asyncio
from urllib.parse import quote_plus

def transliterate_cyrillic(text: str) -> str:
    """Транслитерация кириллицы в латиницу для формирования доменов"""
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    result = ''
    for char in text.lower():
        if char in translit_map:
            result += translit_map[char]
        elif char.isalnum():
            result += char
        elif char in ' -_':
            result += '-'
    return result

class PolzaAIClient:
    def __init__(self):
        self.api_key = os.getenv("POLZA_API_KEY", "ak_FojEdiuKBZJwcAdyGQiPUIKt2DDFsTlawov98zr6Npg")
        self.base_url = "https://api.polza.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Модель для поиска - используем gpt-4o для лучших результатов
        # Альтернативы: gpt-4o, claude-3-5-haiku-20241022
        self.search_model = os.getenv("POLZA_SEARCH_MODEL", "gpt-4o")
    
    async def _make_request(self, prompt: str, max_tokens: int = 2000, model: str = None, retry_count: int = 2) -> str:
        """Универсальный метод для отправки запросов к Polza.AI с retry механизмом"""
        if model is None:
            model = self.search_model
            
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3
        }
        
        last_error = None
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    print(f"Отправляем запрос к Polza.AI (модель: {model}, попытка {attempt + 1}/{retry_count}): {prompt[:100]}...")
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    if "choices" not in result or len(result["choices"]) == 0:
                        raise ValueError("Пустой ответ от API")
                    
                    content = result["choices"][0]["message"]["content"]
                    print(f"✅ Получен ответ от Polza.AI: {content[:100]}...")
                    return content
                    
            except httpx.HTTPStatusError as e:
                last_error = e
                error_msg = f"HTTP {e.response.status_code}"
                if e.response is not None:
                    try:
                        error_data = e.response.json()
                        error_msg = error_data.get("error", {}).get("message", error_msg)
                    except:
                        error_msg = e.response.text[:200]
                
                print(f"⚠️ HTTP ошибка (попытка {attempt + 1}/{retry_count}): {error_msg}")
                
                # Если это ошибка модели, не повторяем
                if e.response.status_code == 400 and "model" in error_msg.lower():
                    raise ValueError(f"Ошибка модели: {error_msg}")
                
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                    continue
                else:
                    raise e
                    
            except httpx.TimeoutException as e:
                last_error = e
                print(f"⚠️ Таймаут (попытка {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise e
                    
            except Exception as e:
                last_error = e
                print(f"⚠️ Ошибка при обращении к Polza.AI (попытка {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise e
        
        # Если все попытки не удались
        raise last_error if last_error else Exception("Неизвестная ошибка")
    
    def _extract_info_from_text(self, text: str, company_name: str) -> Dict[str, Any]:
        """Извлекает информацию о компании из текстового ответа"""
        import re
        
        result = {
            "website": "",
            "email": "",
            "address": "",
            "phone": "",
            "description": "",
            "equipment": "",
            "preferred_language": "ru"  # По умолчанию русский
        }
        
        # Ищем сайт
        website_patterns = [
            r'https?://[^\s\)]+',
            r'www\.[^\s\)]+',
            r'сайт[:\s]+([^\s\)]+)',
            r'website[:\s]+([^\s\)]+)'
        ]
        for pattern in website_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                website = match.group(1) if match.groups() else match.group(0)
                if not website.startswith('http'):
                    website = 'https://' + website
                result["website"] = website
                break
        
        # Ищем email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            result["email"] = email_match.group(0)
        
        # Ищем телефон (международные форматы)
        phone_patterns = [
            r'\+?\d{1,3}[\s\-]?[\(\-]?\d{1,4}[\)\-]?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}',  # Международный формат
            r'\+?7\s?[\(\-]?\d{3}[\)\-]?\s?\d{3}[\-]?\d{2}[\-]?\d{2}',  # Россия
            r'\+?1[\s\-]?[\(\-]?\d{3}[\)\-]?[\s\-]?\d{3}[\-]?\d{4}',  # США/Канада
            r'\+?44[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',  # UK
            r'\+?49[\s\-]?\d{2,4}[\s\-]?\d{3,9}',  # Германия
            r'\+?33[\s\-]?\d{1,2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}',  # Франция
            r'телефон[:\s]+([+\d\s\-\(\)]+)',
            r'phone[:\s]+([+\d\s\-\(\)]+)',
            r'tel[:\s]+([+\d\s\-\(\)]+)'
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phone = match.group(1) if match.groups() else match.group(0)
                result["phone"] = phone.strip()
                break
        
        # Ищем адрес (международные форматы)
        address_patterns = [
            r'адрес[:\s]+([^\n\.]+)',
            r'address[:\s]+([^\n\.]+)',
            r'г\.\s*[А-Яа-я]+[^\n\.]*',  # Россия
            r'Москва[^\n\.]*',
            r'Санкт-Петербург[^\n\.]*',
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)[^\n\.]*',  # Английский
            r'\d+\s+[A-Za-z\s]+(?:Straße|Str|Platz|Weg)[^\n\.]*',  # Немецкий
            r'\d+\s+[A-Za-z\s]+(?:Rue|Avenue|Boulevard|Place)[^\n\.]*',  # Французский
            r'\d+\s+[A-Za-z\s]+(?:Via|Piazza|Corso)[^\n\.]*',  # Итальянский
            r'\d+\s+[A-Za-z\s]+(?:Calle|Avenida|Plaza)[^\n\.]*',  # Испанский
        ]
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                address = match.group(1) if match.groups() else match.group(0)
                result["address"] = address.strip()
                break
        
        # Описание - берем первые несколько предложений
        sentences = re.split(r'[\.!?]\s+', text)
        description_sentences = [s for s in sentences if company_name.lower() in s.lower() or len(s) > 20]
        if description_sentences:
            result["description"] = '. '.join(description_sentences[:3])
        
        return result
    
    def _validate_company_data(self, data: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """Валидация данных компании - проверяем, что данные выглядят реально"""
        validated = {
            "website": "",
            "email": "",
            "address": "",
            "phone": "",
            "description": "",
            "equipment": "",
            "preferred_language": data.get("preferred_language", "ru")
        }
        
        # Проверяем website
        website = data.get("website", "").strip()
        if website and website.startswith("http") and "." in website:
            validated["website"] = website
        
        # Проверяем email
        email = data.get("email", "").strip()
        if email and "@" in email and "." in email.split("@")[1]:
            validated["email"] = email
        
        # Проверяем адрес - должен содержать реальные элементы (поддерживаем международные форматы)
        address = data.get("address", "").strip()
        if address:
            # ОТФИЛЬТРОВЫВАЕМ placeholder'ы и фейковые адреса
            address_lower = address.lower()
            # Проверяем на placeholder'ы типа "Примерная", "Примерный", "Test", "Sample"
            if any(word in address_lower for word in ['примерная', 'примерный', 'пример', 'test', 'sample', 'demo', 'placeholder', 'example']):
                print(f"⚠️ Обнаружен placeholder в адресе: {address}, пропускаем")
            elif any(word in address_lower for word in [
                "г.", "ул.", "д.", "мск", "спб", "москва", "санкт", "проспект", "проезд", "переулок",  # Россия
                "street", "st.", "avenue", "ave.", "road", "rd.", "boulevard", "blvd.",  # Английский
                "strasse", "straße", "platz", "weg",  # Немецкий
                "rue", "avenue", "boulevard", "place",  # Французский
                "via", "piazza", "corso",  # Итальянский
                "calle", "avenida", "plaza",  # Испанский
                "北京", "上海", "广州", "深圳",  # Китай
                "東京", "大阪", "横浜",  # Япония
            ]) or len(address) > 10:  # Если адрес достаточно длинный, считаем его валидным
                validated["address"] = address
        
        # Проверяем телефон - должен содержать цифры и выглядеть как телефон (поддерживаем международные форматы)
        phone = data.get("phone", "").strip()
        if phone and any(char.isdigit() for char in phone) and len(phone) > 7:
            # ОТФИЛЬТРОВЫВАЕМ placeholder'ы и фейковые номера
            phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('x', '').replace('X', '')
            # Проверяем на placeholder'ы типа "123-45-67", "000-00-00", "111-11-11", "+7 (495) 123-45-67", "+7 (XXX) XXX-XX-XX"
            placeholder_patterns = [
                '1234567', '0000000', '1111111', '12345', '00000', '11111',
                '495123', '495000', '495111',  # Москва + placeholder
                'xxx', 'xxx-xx-xx', 'xxx-xxx-xx'  # Шаблоны с XXX
            ]
            if any(pattern in phone_clean.lower() for pattern in placeholder_patterns):
                print(f"⚠️ Обнаружен placeholder в телефоне: {phone}, пропускаем")
            elif phone.startswith('+') or (phone_clean.isdigit() and len(phone_clean) >= 8):
                # Дополнительная проверка: если номер выглядит как пример (495 123-45-67)
                if '+7' in phone and '495' in phone and ('123' in phone_clean or '000' in phone_clean):
                    print(f"⚠️ Обнаружен примерный номер телефона: {phone}, пропускаем")
                else:
                    # Проверяем, что это похоже на телефон (содержит + или достаточно цифр)
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
    
    async def _search_company_via_web(self, company_name: str) -> Dict[str, Any]:
        """Попытка найти информацию о компании через веб-поиск"""
        results = {
            "website": "",
            "email": "",
            "phone": "",
            "address": "",
            "source": "web_search"
        }
        
        try:
            print(f"🌐 Начинаем веб-поиск для компании '{company_name}'...")
            
            # Очищаем название для поиска
            clean_name = company_name.replace('ООО', '').replace('ЗАО', '').replace('АО', '').replace('ИП', '').strip()
            search_queries = [
                f"{clean_name} официальный сайт",
                f"{clean_name} контакты",
                f"{company_name} сайт контакты"
            ]
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # Пробуем несколько поисковых запросов
                for query in search_queries[:2]:  # Ограничиваем до 2 запросов
                    try:
                        encoded_query = quote_plus(query)
                        # Используем DuckDuckGo (не требует API ключа)
                        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                        
                        response = await client.get(url, headers=headers, timeout=10.0)
                        
                        if response.status_code == 200:
                            content = response.text
                            content_lower = content.lower()
                            
                            # Ищем сайты (более точные паттерны)
                            website_patterns = [
                                r'https?://(?:www\.)?([a-z0-9\-]+\.(?:ru|com|org|net|io|co))',
                                r'www\.([a-z0-9\-]+\.(?:ru|com|org|net|io|co))',
                                r'([a-z0-9\-]+\.(?:ru|com|org|net|io|co))',
                            ]
                            
                            # Ищем email
                            email_pattern = r'\b([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})\b'
                            
                            # Ищем телефоны
                            phone_patterns = [
                                r'\+7\s?\(?\d{3}\)?\s?\d{3}[- ]?\d{2}[- ]?\d{2}',
                                r'\+7\s?\d{10}',
                                r'8\s?\(?\d{3}\)?\s?\d{3}[- ]?\d{2}[- ]?\d{2}',
                            ]
                            
                            # Ищем адреса (российские форматы)
                            address_patterns = [
                                r'(?:г\.|город)\s+[А-ЯЁа-яё\s]+(?:ул\.|улица|проспект|пр\.|переулок|пер\.)\s+[А-ЯЁа-яё\s]+(?:д\.|дом)\s*\d+',
                                r'[А-ЯЁа-яё]+\s*область[,\s]+[А-ЯЁа-яё]+\s*район[,\s]+[А-ЯЁа-яё]+',
                            ]
                            
                            # Ищем website
                            # Список доменов для исключения (поисковики, соцсети, общие домены)
                            excluded_domains = [
                                'google', 'yandex', 'duckduckgo', 'facebook', 'twitter', 'linkedin',
                                'w3.org', 'wikipedia', 'wikimedia', 'github', 'stackoverflow',
                                'reddit', 'youtube', 'instagram', 'vk.com', 'ok.ru',
                                'mail.ru', 'rambler', 'livejournal', 'habr', 'geektimes'
                            ]
                            
                            # Пытаемся найти домен, связанный с названием компании
                            company_name_clean_lower = clean_name.lower().replace(' ', '').replace('-', '')
                            company_keywords = [kw for kw in company_name_clean_lower.split() if len(kw) > 3]
                            
                            for pattern in website_patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    website = match.group(1) if match.groups() else match.group(0)
                                    website_lower = website.lower()
                                    
                                    # Фильтруем нерелевантные домены
                                    if any(skip in website_lower for skip in excluded_domains):
                                        continue
                                    
                                    # Приоритет: домены, содержащие ключевые слова из названия компании
                                    is_relevant = any(kw in website_lower for kw in company_keywords) if company_keywords else True
                                    
                                    if is_relevant or not results["website"]:
                                        if not website.startswith('http'):
                                            website = 'https://' + website
                                        results["website"] = website
                                        print(f"✅ Найден сайт через веб-поиск: {website}")
                                        if is_relevant:
                                            break  # Нашли релевантный домен - прекращаем поиск
                                if results["website"] and any(kw in results["website"].lower() for kw in company_keywords):
                                    break
                            
                            # Ищем email
                            if not results["email"]:
                                email_matches = re.finditer(email_pattern, content, re.IGNORECASE)
                                for match in email_matches:
                                    email = match.group(1)
                                    # Фильтруем нерелевантные email
                                    if not any(skip in email.lower() for skip in ['example', 'test', 'sample', 'placeholder']):
                                        results["email"] = email
                                        print(f"✅ Найден email через веб-поиск: {email}")
                                        break
                            
                            # Ищем телефон
                            if not results["phone"]:
                                for pattern in phone_patterns:
                                    phone_match = re.search(pattern, content, re.IGNORECASE)
                                    if phone_match:
                                        phone = phone_match.group(0).strip()
                                        # Фильтруем placeholder'ы
                                        phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                                        if not any(p in phone_clean for p in ['1234567', '0000000', '1111111']):
                                            results["phone"] = phone
                                            print(f"✅ Найден телефон через веб-поиск: {phone}")
                                            break
                            
                            # Если нашли достаточно информации, прекращаем поиск
                            if results["website"] or results["email"]:
                                break
                                
                    except Exception as e:
                        print(f"⚠️ Ошибка при запросе '{query}': {e}")
                        continue
                        
        except Exception as e:
            print(f"⚠️ Общая ошибка при веб-поиске: {e}")
        
        if results["website"] or results["email"] or results["phone"]:
            print(f"✅ Веб-поиск завершен: найдено {sum(1 for v in [results['website'], results['email'], results['phone']] if v)} полей")
            return results
        else:
            print(f"⚠️ Веб-поиск не дал результатов для '{company_name}'")
            return {}
    
    async def search_company_info(self, company_name: str, retry_count: int = 3) -> Dict[str, Any]:
        """Поиск информации о компании через Polza.AI с retry механизмом и улучшенной обработкой"""
        
        # Очищаем название компании от лишних символов
        company_name_clean = company_name.strip()
        
        # Сначала пробуем найти через веб-поиск
        web_results = await self._search_company_via_web(company_name_clean)
        web_context = ""
        if web_results.get("website") or web_results.get("email") or web_results.get("phone"):
            web_context = f"\n\n⚠️⚠️⚠️ КРИТИЧЕСКИ ВАЖНО - РЕАЛЬНЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА: ⚠️⚠️⚠️\n"
            web_context += "Ниже приведены РЕАЛЬНЫЕ данные, найденные через веб-поиск в интернете.\n"
            web_context += "Ты ОБЯЗАН использовать ЭТИ данные, а НЕ придумывать свои!\n\n"
            if web_results.get("website"):
                web_context += f"РЕАЛЬНЫЙ САЙТ (найден в интернете): {web_results.get('website')}\n"
            if web_results.get("email"):
                web_context += f"РЕАЛЬНЫЙ EMAIL (найден в интернете): {web_results.get('email')}\n"
            if web_results.get("phone"):
                web_context += f"РЕАЛЬНЫЙ ТЕЛЕФОН (найден в интернете): {web_results.get('phone')}\n"
            web_context += "\nИСПОЛЬЗУЙ ТОЛЬКО ЭТИ ДАННЫЕ! НЕ ПРИДУМЫВАЙ ДРУГИЕ!\n"
            web_context += "Если данных нет выше - оставь поле ПУСТЫМ!\n\n"
        
        # Промпт с четкой структурой и инструкциями
        prompt = f"""Ты - профессиональный исследователь компаний. Твоя задача - найти информацию о компании "{company_name_clean}".
{web_context}
КРИТИЧЕСКИ ВАЖНО - ЧЕСТНОСТЬ ДАННЫХ:
- НИКОГДА не придумывай данные, которых не знаешь!
- НЕ используй placeholder'ы типа "123-45-67", "Примерная улица", "Примерный адрес", "г. Москва, ул. Примерная"
- НЕ придумывай телефоны типа "+7 (495) 123-45-67" или "+7 (XXX) XXX-XX-XX"
- НЕ придумывай адреса типа "г. Москва, ул. Примерная, д. 1" или "Россия, Москва, ул. Примерная"
- Если не знаешь точный телефон или адрес - оставь поле ПУСТЫМ (пустая строка "")
- Заполняй только те поля, которые ты РЕАЛЬНО знаешь или можешь логически вывести из названия
- Если выше есть информация из веб-поиска - используй ТОЛЬКО её!
- Если веб-поиск не нашел телефон или адрес - оставь их ПУСТЫМИ, НЕ ПРИДУМЫВАЙ!

ИНСТРУКЦИИ:
1. Используй свои знания о РЕАЛЬНЫХ компаниях
2. Если компания известная - используй актуальные данные
3. Если компания неизвестная:
   - Можешь составить website и email на основе названия (это логично)
   - НО НЕ придумывай телефон и адрес, если не знаешь точно
   - Опиши деятельность на основе названия (это логично)
4. Всегда возвращай валидный JSON

ТРЕБОВАНИЯ К ДАННЫМ:

1. Website (сайт):
   - Формат: https://домен.ру или https://домен.com
   - Можешь составить на основе названия компании (это нормально)
   - Примеры: 
     * "Алмазгеобур" → https://almazgeobur.ru
     * "ООО Рога и Копыта" → https://rogaikopyta.ru
   - Убери из названия: ООО, ЗАО, АО, ИП, Ltd, Inc
   - Транслитерируй кириллицу в латиницу
   - Если не можешь составить - оставь пустым

2. Email:
   - Формат: стандартный email адрес
   - Составь на основе домена из website
   - Варианты: info@, contact@, sales@, office@
   - Пример: если website = https://almazgeobur.ru, то email = info@almazgeobur.ru
   - Если нет website - оставь пустым

3. Phone (телефон):
   - Формат: +7 (XXX) XXX-XX-XX для России
   - Или международный формат: +код страны номер
   - КРИТИЧЕСКИ ВАЖНО: Если выше нет РЕАЛЬНОГО телефона из веб-поиска - оставь ПУСТЫМ!
   - НЕ ПРИДУМЫВАЙ! НЕ используй примеры типа "+7 (495) 123-45-67" или "+7 (XXX) XXX-XX-XX"
   - НЕ используй placeholder'ы типа "123-45-67", "000-00-00", "111-11-11"
   - Если не знаешь - ВСЕГДА оставляй пустым: ""

4. Address (адрес):
   - Полный адрес с городом и страной
   - Для российских компаний: город, улица, дом
   - КРИТИЧЕСКИ ВАЖНО: Если выше нет РЕАЛЬНОГО адреса из веб-поиска - оставь ПУСТЫМ!
   - НЕ ПРИДУМЫВАЙ! НЕ используй примеры типа "г. Москва, ул. Примерная, д. 1"
   - НЕ используй placeholder'ы типа "Примерная улица", "Примерный адрес", "Test", "Sample"
   - Если не знаешь - ВСЕГДА оставляй пустым: ""

5. Description (описание) - ОБЯЗАТЕЛЬНО:
   - Краткое описание деятельности компании (2-3 предложения)
   - На основе названия определи вероятную сферу деятельности
   - Опиши что делает компания
   - Это можно логически вывести из названия

6. Equipment (оборудование):
   - Какое оборудование или технологии использует компания
   - На основе сферы деятельности
   - Если не знаешь - можешь оставить пустым

7. Preferred_language (язык):
   - "ru" для российских компаний
   - "en" для международных/англоязычных
   - По умолчанию "ru"

КРИТИЧЕСКИ ВАЖНО:
- ВСЕГДА возвращай валидный JSON
- НЕ придумывай телефон и адрес, если не знаешь точно - оставь ПУСТЫМИ
- Заполняй website, email и description (это можно логически вывести)
- НЕ возвращай текст вне JSON
- НЕ объясняй, просто верни JSON

ФОРМАТ ОТВЕТА (строго JSON, без дополнительного текста):
{{
    "website": "https://almazgeobur.ru",
    "email": "info@almazgeobur.ru",
    "address": "",
    "phone": "",
    "description": "описание деятельности (ОБЯЗАТЕЛЬНО)",
    "equipment": "оборудование или технологии",
    "preferred_language": "ru"
}}"""
        
        last_error = None
        for attempt in range(retry_count):
            try:
                print(f"Попытка {attempt + 1}/{retry_count} поиска информации о компании '{company_name_clean}'")
                
                # Делаем запрос с увеличенным таймаутом
                content = await self._make_request(prompt, max_tokens=2000, model='gpt-4o')
                
                # Проверяем на отказ модели
                if any(phrase in content.lower() for phrase in ["sorry", "can't", "cannot", "не могу", "не имею"]):
                    if attempt < retry_count - 1:
                        print(f"Модель отказалась, пробуем упрощенный запрос (попытка {attempt + 2})...")
                        # Упрощенный промпт
                        simple_prompt = f"""Найди информацию о компании "{company_name_clean}". Верни ТОЛЬКО JSON без дополнительного текста:
{{
    "website": "",
    "email": "",
    "address": "",
    "phone": "",
    "description": "краткое описание",
    "equipment": "",
    "preferred_language": "ru"
}}"""
                        content = await self._make_request(simple_prompt, max_tokens=1000, model='gpt-4o')
                    else:
                        # Последняя попытка - используем fallback
                        print("Используем fallback стратегию...")
                        return self._generate_fallback_company_data(company_name_clean)
                
                # Извлекаем JSON из ответа
                result = self._extract_json_from_response(content, company_name_clean)
                
                # ПРИОРИТЕТ: Используем данные из веб-поиска, если они есть
                # И ОБЯЗАТЕЛЬНО очищаем придуманные данные, если веб-поиск их не нашел
                if web_results:
                    # Перезаписываем данными из веб-поиска (они имеют приоритет)
                    if web_results.get("website"):
                        result["website"] = web_results.get("website")
                        print(f"✅ Используем сайт из веб-поиска: {web_results.get('website')}")
                    if web_results.get("email"):
                        result["email"] = web_results.get("email")
                        print(f"✅ Используем email из веб-поиска: {web_results.get('email')}")
                    if web_results.get("phone"):
                        result["phone"] = web_results.get("phone")
                        print(f"✅ Используем телефон из веб-поиска: {web_results.get('phone')}")
                    else:
                        # Если веб-поиск не нашел телефон - очищаем придуманный
                        if result.get("phone"):
                            phone_clean = result.get("phone", "").replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                            if any(p in phone_clean for p in ['1234567', '0000000', '1111111', '495123', 'xxx']):
                                print(f"⚠️ Очищаем придуманный телефон: {result.get('phone')}")
                                result["phone"] = ""
                    
                    if web_results.get("address"):
                        result["address"] = web_results.get("address")
                        print(f"✅ Используем адрес из веб-поиска: {web_results.get('address')}")
                    else:
                        # Если веб-поиск не нашел адрес - очищаем придуманный
                        if result.get("address"):
                            address_lower = result.get("address", "").lower()
                            if any(word in address_lower for word in ['примерная', 'примерный', 'пример', 'test', 'sample']):
                                print(f"⚠️ Очищаем придуманный адрес: {result.get('address')}")
                                result["address"] = ""
                
                # Валидируем данные
                validated_result = self._validate_company_data(result, company_name_clean)
                validated_result["name"] = company_name_clean
                
                # Проверяем, что получили хотя бы минимальные данные
                if validated_result.get("description") or validated_result.get("website"):
                    print(f"✅ Успешно найдена информация о компании '{company_name_clean}'")
                    return validated_result
                else:
                    print(f"⚠️ Получены пустые данные, пробуем еще раз...")
                    if attempt < retry_count - 1:
                        continue
                    else:
                        return validated_result
                        
            except httpx.HTTPError as e:
                last_error = e
                print(f"HTTP ошибка при попытке {attempt + 1}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                    continue
                else:
                    break
            except json.JSONDecodeError as e:
                last_error = e
                print(f"Ошибка парсинга JSON при попытке {attempt + 1}: {e}")
                if attempt < retry_count - 1:
                    continue
                else:
                    # Пытаемся извлечь из текста
                    result = self._extract_info_from_text(content if 'content' in locals() else "", company_name_clean)
                    validated_result = self._validate_company_data(result, company_name_clean)
                    validated_result["name"] = company_name_clean
                    return validated_result
            except Exception as e:
                last_error = e
                print(f"Неожиданная ошибка при попытке {attempt + 1}: {e}")
                import traceback
                traceback.print_exc()
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    break
        
        # Если все попытки не удались, возвращаем fallback данные
        print(f"❌ Все попытки не удались для компании '{company_name_clean}', используем fallback")
        return self._generate_fallback_company_data(company_name_clean)
    
    def _extract_json_from_response(self, content: str, company_name: str) -> Dict[str, Any]:
        """Извлекает JSON из ответа модели с улучшенной обработкой"""
        # Убираем markdown форматирование если есть
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Ищем JSON объект
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            try:
                result = json.loads(json_str)
                print(f"✅ JSON успешно извлечен из ответа")
                return result
            except json.JSONDecodeError as e:
                print(f"⚠️ Ошибка парсинга JSON: {e}")
                print(f"Пробуем исправить JSON...")
                # Пытаемся исправить распространенные ошибки
                json_str = self._fix_json_string(json_str)
                try:
                    return json.loads(json_str)
                except:
                    pass
        
        # Если не удалось извлечь JSON, пытаемся из текста
        print(f"⚠️ JSON не найден, извлекаем из текста...")
        return self._extract_info_from_text(content, company_name)
    
    def _fix_json_string(self, json_str: str) -> str:
        """Исправляет распространенные ошибки в JSON строке"""
        # Убираем trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        # Исправляем одинарные кавычки
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
        return json_str
    
    def _generate_fallback_company_data(self, company_name: str) -> Dict[str, Any]:
        """Генерирует базовые данные компании на основе названия (fallback)"""
        print(f"Генерируем fallback данные для '{company_name}'")
        
        # Очищаем название от организационных форм
        clean_name = company_name.replace('ООО', '').replace('ЗАО', '').replace('АО', '').replace('ИП', '').replace('Ltd', '').replace('Inc', '').strip()
        
        # Пытаемся определить сферу деятельности по названию
        name_lower = clean_name.lower()
        description = ""
        equipment = ""
        
        if any(word in name_lower for word in ['алмаз', 'алроса', 'добыч', 'шахт', 'руд', 'гео', 'бур', 'разведк']):
            description = f"{company_name} - компания в сфере геологоразведки, бурения и добычи полезных ископаемых. Специализируется на алмазном бурении и геологических исследованиях."
            equipment = "Алмазные буровые установки, геологоразведочное оборудование, горнодобывающее оборудование"
        elif any(word in name_lower for word in ['банк', 'финанс', 'кредит']):
            description = f"{company_name} - финансовая организация, предоставляющая банковские и финансовые услуги"
            equipment = "IT-инфраструктура, системы безопасности, банковское оборудование"
        elif any(word in name_lower for word in ['нефть', 'газ', 'энерг']):
            description = f"{company_name} - энергетическая компания, занимающаяся добычей и переработкой нефти и газа"
            equipment = "Нефтегазовое оборудование, трубопроводы, буровые установки"
        elif any(word in name_lower for word in ['строитель', 'строй', 'ремонт']):
            description = f"{company_name} - строительная компания, выполняющая строительно-монтажные работы"
            equipment = "Строительная техника, инструменты, подъемное оборудование"
        else:
            description = f"{company_name} - компания, деятельность которой требует уточнения. Рекомендуется связаться с компанией для получения подробной информации."
            equipment = "Оборудование и технологии в зависимости от сферы деятельности"
        
        # Генерируем домен на основе названия
        domain_base = transliterate_cyrillic(clean_name)
        # Убираем пробелы и дефисы, оставляем только буквы и цифры
        domain_base = re.sub(r'[^a-z0-9]', '', domain_base.lower())
        
        website = ""
        email = ""
        if domain_base and len(domain_base) > 2:
            # Пробуем разные варианты доменов
            website = f"https://{domain_base}.ru"
            email = f"info@{domain_base}.ru"
        else:
            # Если не удалось составить домен, используем общий формат
            website = f"https://{clean_name.lower().replace(' ', '').replace('-', '')}.ru"
            email = f"info@{clean_name.lower().replace(' ', '').replace('-', '')}.ru"
        
        return {
            "name": company_name,
            "website": website,
            "email": email,
            "address": "",
            "phone": "",
            "description": description,
            "equipment": equipment,
            "preferred_language": "ru"
        }
    
    async def search_companies_by_equipment(self, equipment_name: str) -> List[Dict[str, Any]]:
        """Поиск компаний, которые купили определенное оборудование через интернет"""
        
        prompt = f"""Ты - эксперт по поиску компаний в интернете. Твоя задача - найти РЕАЛЬНЫЕ компании, которые используют оборудование "{equipment_name}".

ВАЖНО: Ты должен использовать свои знания и логику для поиска компаний. Если пользователь указал страну (например, "в России"), ищи компании именно в этой стране.

Для каждой найденной компании найди:
1. Название компании (обязательно)
2. Официальный сайт (если можешь логически предположить на основе названия)
3. Контактный email (обычно info@[домен], contact@[домен] или sales@[домен])
4. Адрес компании (с указанием страны и города)
5. Телефон (в международном формате с кодом страны)
6. Краткое описание деятельности

ИНСТРУКЦИИ:
- ИСПОЛЬЗУЙ свои знания о компаниях, которые реально используют такое оборудование
- Если указана страна (например, "в России", "в США") - ищи компании именно в этой стране
- Если информации о контактах нет, но ты можешь логически предположить (например, сайт на основе названия) - укажи это
- НЕ возвращай пустой массив, если знаешь хотя бы несколько компаний
- Найди минимум 5-10 компаний (или столько, сколько знаешь)
- Для адреса: укажи полный адрес с указанием страны, города, улицы
- Для телефона: используй международный формат с кодом страны (например, +7 для России, +1 для США, +44 для UK)

Ответь ТОЛЬКО в формате JSON массива без дополнительного текста:
[
    {{
        "name": "Название компании",
        "website": "https://example.com",
        "email": "email@example.com",
        "address": "полный адрес с указанием страны",
        "phone": "телефон в международном формате",
        "description": "описание деятельности"
    }}
]"""
        
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
    
    def _extract_company_names_from_message(self, message: str) -> List[str]:
        """Извлекает названия компаний из сообщения пользователя"""
        import re
        
        companies = []
        message_lower = message.lower()
        
        # Проверяем, есть ли упоминание компаний или запрос на поиск
        company_keywords = ['компани', 'фирм', 'организац', 'предприяти', 'ооо', 'зао', 'ао', 'ип', 
                           'найди', 'найти', 'ищу', 'искать', 'информация', 'знаешь', 'расскажи']
        
        if any(word in message_lower for word in company_keywords):
            # Паттерны для поиска компаний (в порядке приоритета)
            patterns = [
                # Прямые запросы: "найди информацию о компании X"
                r'(?:найди|найти|ищу|искать|расскажи|что\s+ты\s+знаешь)\s+(?:информацию\s+)?(?:о\s+)?(?:компани[ияюе]|фирм[еыу]|организаци[июе])\s+["\']?([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]+)["\']?',
                # "компания X" или "фирма X"
                r'(?:компани[яиюе]|фирм[аыуе]|организаци[яиюе]|предприяти[еяю])\s+["\']?([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]+(?:ООО|ЗАО|АО|ИП|Ltd|Inc|LLC|GmbH|Corp)?)["\']?',
                # "ООО X", "ЗАО X" и т.д.
                r'(?:ООО|ЗАО|АО|ИП|Ltd|Inc|LLC|GmbH|Corp)\s+["\']?([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]+)["\']?',
                # Названия в кавычках
                r'["\']([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]+(?:ООО|ЗАО|АО|ИП|Ltd|Inc|LLC|GmbH|Corp)?)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    company = match.strip()
                    # Очищаем от лишних слов
                    company = re.sub(r'\s+(компани[ияюе]|фирм[ыуе]|организаци[июе]|предприяти[еяю])\s*$', '', company, flags=re.IGNORECASE)
                    company = company.strip('.,!?;:')
                    
                    if len(company) > 2 and len(company) < 200:
                        # Проверяем, что это не просто общее слово
                        if not company.lower() in ['информация', 'компания', 'фирма', 'организация', 'предприятие']:
                            companies.append(company)
            
            # Если не нашли по паттернам, но есть упоминание компаний, пробуем извлечь после ключевых слов
            if not companies:
                # Ищем текст после "о компании", "фирма" и т.д.
                fallback_patterns = [
                    r'(?:о|про)\s+(?:компани[ияюе]|фирм[еыу]|организаци[июе])\s+([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]{3,50})',
                    r'(?:компани[ияюе]|фирм[аыуе])\s+([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]{3,50})',
                ]
                for pattern in fallback_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        company = match.group(1).strip().strip('.,!?;:')
                        if len(company) > 2 and len(company) < 200:
                            companies.append(company)
                            break
        
        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        unique_companies = []
        for company in companies:
            company_lower = company.lower().strip()
            if company_lower not in seen and len(company_lower) > 2:
                seen.add(company_lower)
                unique_companies.append(company)
        
        return unique_companies[:5]  # Максимум 5 компаний за раз
    
    def _extract_equipment_from_message(self, message: str) -> str:
        """Извлекает название оборудования из сообщения"""
        import re
        
        message_lower = message.lower()
        
        # Проверяем, есть ли упоминание оборудования или запрос на поиск компаний по оборудованию
        equipment_keywords = ['оборудован', 'техник', 'использует', 'пользуется', 'применяет', 'имеет', 'работает с', 'используют']
        search_keywords = ['найди', 'найти', 'ищу', 'искать', 'кто', 'какие компании']
        
        has_search = any(word in message_lower for word in search_keywords)
        has_equipment = any(word in message_lower for word in equipment_keywords)
        
        # Если есть ключевые слова поиска И упоминание использования оборудования
        if has_search and has_equipment:
            # Упрощенный подход: ищем текст после "используют" или "использует"
            # Паттерн: все что идет после "используют" до конца строки или до знаков препинания
            simple_patterns = [
                r'(?:используют?|пользуются?|применяют?|имеют?|работают?\s+с)\s+["\']?([^"\'\n\.!?]{3,100})["\']?',
            ]
            
            for pattern in simple_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    equipment = match.group(1).strip().strip('.,!?;:')
                    # Очищаем от лишних слов в конце
                    equipment = re.sub(r'\s+(оборудован[иемя]|техник[аой]|компани[ияюе]|фирм[ыуе]|используют?|пользуются?)\s*$', '', equipment, flags=re.IGNORECASE)
                    # Убираем фразы типа "которые используют" в начале
                    equipment = re.sub(r'^(?:котор[ыеая]|кто)\s+(?:используют?|пользуются?)\s+', '', equipment, flags=re.IGNORECASE)
                    equipment = equipment.strip()
                    if len(equipment) > 2 and len(equipment) < 200:
                        print(f"Обнаружено упоминание оборудования: {equipment}")
                        return equipment
        
        # Также проверяем паттерн "компании с оборудованием X"
        if any(word in message_lower for word in equipment_keywords):
            pattern = r'(?:компани[ияюе]|фирм[ыуе])\s+(?:с\s+)?(?:оборудованием|техникой)\s+["\']?([А-ЯЁA-Z][А-Яа-яёA-Za-z0-9\s\-\.]+)["\']?'
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                equipment = match.group(1).strip().strip('.,!?;:')
                if len(equipment) > 2 and len(equipment) < 200:
                    return equipment
        
        return None
    
    async def chat_with_llm(self, message: str, conversation_history: List[Dict[str, Any]] = None, custom_settings: Dict[str, Any] = None) -> str:
        """Общение с LLM в режиме чата с автоматическим поиском информации о компаниях"""
        
        # СНАЧАЛА проверяем запрос на поиск по оборудованию (это приоритетнее)
        equipment_name = self._extract_equipment_from_message(message)
        
        # ТОЛЬКО ЕСЛИ это не запрос на поиск по оборудованию, ищем названия компаний
        company_names = []
        if not equipment_name:
            company_names = self._extract_company_names_from_message(message)
            
            # Если не нашли компанию по паттернам, но сообщение короткое и начинается с заглавной буквы,
            # возможно это просто название компании
            if not company_names and len(message.strip()) < 100:
                message_stripped = message.strip()
                # Проверяем, начинается ли с заглавной буквы и содержит ли буквы
                if message_stripped and message_stripped[0].isupper() and any(c.isalpha() for c in message_stripped):
                    # Проверяем, не является ли это вопросом
                    if not any(word in message_stripped.lower() for word in ['?', 'как', 'что', 'где', 'когда', 'почему', 'зачем']):
                        # Проверяем, не содержит ли это слова, указывающие на поиск по оборудованию
                        if not any(word in message_stripped.lower() for word in ['использует', 'пользуется', 'применяет', 'оборудован', 'техник']):
                            # Возможно, это просто название компании
                            if len(message_stripped) > 2 and len(message_stripped) < 100:
                                company_names = [message_stripped]
                                print(f"Предполагаем, что '{message_stripped}' - это название компании")
        
        # Собираем информацию о компаниях, если они упомянуты
        company_info_context = ""
        if company_names:
            print(f"🔍 Обнаружены упоминания компаний в сообщении: {company_names}")
            for company_name in company_names:
                try:
                    print(f"🔍 Начинаем поиск информации о компании '{company_name}'...")
                    # Используем улучшенный поиск с retry, но с ограничением времени
                    try:
                        company_info = await asyncio.wait_for(
                            self.search_company_info(company_name, retry_count=2),
                            timeout=60.0  # Максимум 60 секунд на поиск
                        )
                        print(f"✅ Поиск информации о компании '{company_name}' завершен")
                        if company_info:
                            info_text = f"\n\n## Информация о компании '{company_name}':\n"
                            if company_info.get("website"):
                                info_text += f"- **Сайт**: {company_info.get('website')}\n"
                            if company_info.get("email"):
                                info_text += f"- **Email**: {company_info.get('email')}\n"
                            
                            # ФИЛЬТРАЦИЯ: Проверяем телефон на placeholder'ы перед добавлением
                            phone = company_info.get("phone", "").strip()
                            if phone:
                                phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('x', '').replace('X', '')
                                placeholder_patterns = [
                                    '1234567', '0000000', '1111111', '12345', '00000', '11111',
                                    '495123', '495000', '495111', 'xxx', 'xxx-xx-xx'
                                ]
                                if not any(pattern in phone_clean.lower() for pattern in placeholder_patterns):
                                    if not ('+7' in phone and '495' in phone and ('123' in phone_clean or '000' in phone_clean)):
                                        info_text += f"- **Телефон**: {phone}\n"
                                    else:
                                        print(f"⚠️ Пропускаем примерный телефон в чате: {phone}")
                                else:
                                    print(f"⚠️ Пропускаем placeholder телефон в чате: {phone}")
                            
                            # ФИЛЬТРАЦИЯ: Проверяем адрес на placeholder'ы перед добавлением
                            address = company_info.get("address", "").strip()
                            if address:
                                address_lower = address.lower()
                                if not any(word in address_lower for word in ['примерная', 'примерный', 'пример', 'test', 'sample', 'demo', 'placeholder']):
                                    info_text += f"- **Адрес**: {address}\n"
                                else:
                                    print(f"⚠️ Пропускаем placeholder адрес в чате: {address}")
                            
                            if company_info.get("description"):
                                info_text += f"- **Описание**: {company_info.get('description')}\n"
                            if company_info.get("equipment"):
                                info_text += f"- **Оборудование**: {company_info.get('equipment')}\n"
                            company_info_context += info_text
                        else:
                            print(f"⚠️ Не удалось получить информацию о компании '{company_name}'")
                            company_info_context += f"\n\n## Информация о компании '{company_name}':\n"
                            company_info_context += f"- К сожалению, не удалось найти полную информацию о компании. Попробуйте уточнить запрос.\n"
                    except asyncio.TimeoutError:
                        print(f"⏱️ Таймаут при поиске информации о компании '{company_name}' (превышено 60 секунд)")
                        company_info_context += f"\n\n## Информация о компании '{company_name}':\n"
                        company_info_context += f"- Поиск информации занял слишком много времени. Попробуйте уточнить название компании или повторить запрос позже.\n"
                except Exception as e:
                    print(f"❌ Ошибка при поиске информации о компании {company_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Добавляем базовую информацию даже при ошибке
                    company_info_context += f"\n\n## Информация о компании '{company_name}':\n"
                    company_info_context += f"- Произошла ошибка при поиске информации. Попробуйте уточнить запрос или повторить позже.\n"
        
        # Если упомянуто оборудование, ищем компании
        equipment_companies_context = ""
        if equipment_name:
            print(f"Обнаружено упоминание оборудования: {equipment_name}")
            try:
                # Проверяем, указана ли страна в запросе
                country_mentioned = ""
                if "в россии" in message.lower() or "россия" in message.lower():
                    country_mentioned = " в России"
                elif "в сша" in message.lower() or "сша" in message.lower():
                    country_mentioned = " в США"
                elif "в германии" in message.lower() or "германия" in message.lower():
                    country_mentioned = " в Германии"
                
                # Добавляем страну к названию оборудования для поиска
                search_query = equipment_name + country_mentioned if country_mentioned else equipment_name
                companies = await self.search_companies_by_equipment(search_query)
                if companies:
                    equipment_companies_context = f"\n\n## Компании, использующие '{equipment_name}'{country_mentioned}:\n\n"
                    for i, company in enumerate(companies[:10], 1):  # Максимум 10 компаний
                        equipment_companies_context += f"{i}. **{company.get('name', 'Неизвестно')}**\n"
                        if company.get("website"):
                            equipment_companies_context += f"   - Сайт: {company.get('website')}\n"
                        if company.get("email"):
                            equipment_companies_context += f"   - Email: {company.get('email')}\n"
                        if company.get("phone"):
                            equipment_companies_context += f"   - Телефон: {company.get('phone')}\n"
                        if company.get("address"):
                            equipment_companies_context += f"   - Адрес: {company.get('address')}\n"
                        equipment_companies_context += "\n"
            except Exception as e:
                print(f"Ошибка при поиске компаний по оборудованию {equipment_name}: {e}")
        
        # Формируем контекст для чата
        system_prompt = """Ты - умный AI агент-помощник по поиску информации о компаниях и оборудовании по всему миру. 
        Ты имеешь доступ ко всему приложению и можешь самостоятельно выполнять действия.
        
        КРИТИЧЕСКИ ВАЖНО - ФОРМАТ ОТВЕТОВ:
        - НИКОГДА не говори "подождите" или "сейчас найду" - информация УЖЕ найдена и передана тебе в контексте!
        - ВСЕГДА давай ПОЛНЫЙ ответ сразу с ВСЕЙ найденной информацией
        - Если в контексте есть информация о компании - ОБЯЗАТЕЛЬНО используй её в ответе
        - Структурируй ответ с заголовками и списками
        - Показывай ВСЕ найденные данные: сайт, email, телефон (если есть), адрес (если есть), описание, оборудование
        - НИКОГДА не придумывай телефон или адрес, если их нет в контексте - просто не указывай эти поля!
        - НЕ используй placeholder'ы типа "+7 (495) 123-45-67" или "г. Москва, ул. Примерная" - это придуманные данные!
        
        ВАЖНЫЕ ВОЗМОЖНОСТИ И ФУНКЦИИ АГЕНТА:
        
        1. АВТОМАТИЧЕСКИЙ ПОИСК И СОХРАНЕНИЕ КОМПАНИЙ:
           - Когда пользователь просит найти и сохранить компанию, ты автоматически:
             * Ищешь информацию о компании через интернет
             * Сохраняешь найденные данные в базу данных
           - Команды для сохранения: "найди и сохрани компанию X", "добавь компанию Y в базу", "запиши информацию о Z"
        
        2. ПОИСК ИНФОРМАЦИИ О КОМПАНИЯХ:
           - Автоматически ищешь информацию о компаниях, когда пользователь спрашивает о них
           - Находишь: сайт, email, телефон, адрес, описание, оборудование
           - ВСЕГДА показывай найденную информацию в ответе
        
        3. ПОИСК ПО ОБОРУДОВАНИЮ:
           - Можешь искать компании, которые используют определенное оборудование
           - Поддерживается указание страны (например, "в России", "в США")
        
        4. ВЗАИМОДЕЙСТВИЕ С БАЗОЙ ДАННЫХ:
           - Можешь автоматически сохранять найденные компании в базу данных
           - Можешь искать компании в базе данных
           - Можешь обновлять информацию о компаниях
        
        5. EMAIL РАССЫЛКА И ПРОВЕРКА:
           - Можешь проверять email адреса на валидность
           - Можешь создавать email рассылки
           - Можешь отправлять письма компаниям
        
        ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ:
        - Когда пользователь просит найти информацию о компании, информация УЖЕ найдена и передана в контексте
        - ВСЕГДА давай полный ответ с ВСЕЙ найденной информацией сразу
        - НЕ говори "подождите" или "сейчас найду" - информация уже есть!
        - Отвечай на русском языке, будь полезным и информативным
        - Форматируй ответы в Markdown для лучшей читаемости
        - Используй заголовки (## ###) для структурирования
        - Используй списки (- или 1.) для перечислений
        - Выделяй важные моменты **жирным** или *курсивом*
        - Если в контексте есть информация о компании - ОБЯЗАТЕЛЬНО покажи её полностью
        
        ФОРМАТ ОТВЕТА ПРИ НАЙДЕННОЙ ИНФОРМАЦИИ О КОМПАНИИ:
        ## Информация о компании "[Название]"
        
        - **Сайт**: [ссылка](url) или текст
        - **Email**: email@domain.com
        - **Телефон**: +7 (XXX) XXX-XX-XX (если есть)
        - **Адрес**: полный адрес (если есть)
        - **Описание**: полное описание деятельности
        - **Оборудование**: используемое оборудование (если есть)
        
        ПРИМЕРЫ КОМАНД:
        - "Найди и сохрани компанию ООО Рога и Копыта" → найдешь информацию и сохранишь в БД
        - "Поищи информацию о компании Газпром" → найдешь информацию и ПОКАЖЕШЬ ВСЮ найденную информацию сразу
        - "Найди компании, использующие станки в России" → найдешь список компаний
        - "Проверь email адреса всех компаний" → проверишь все email в базе"""
        
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
        
        # Формируем сообщение пользователя с контекстом найденной информации
        user_message = message
        if company_info_context:
            # Добавляем четкую инструкцию использовать найденную информацию
            user_message += f"\n\n{company_info_context}\n\nВАЖНО: Информация о компании УЖЕ найдена выше. Дай ПОЛНЫЙ ответ с ВСЕЙ этой информацией сразу. НЕ говори 'подождите' или 'сейчас найду' - информация уже есть!"
        if equipment_companies_context:
            user_message += equipment_companies_context
        
        # Добавляем текущее сообщение пользователя с контекстом
        messages.append({"role": "user", "content": user_message})
        
        # Используем кастомные настройки или значения по умолчанию
        model = custom_settings.get('model', 'gpt-4o') if custom_settings else 'gpt-4o'
        # Увеличиваем max_tokens для полных ответов с информацией о компаниях
        max_tokens = custom_settings.get('max_tokens', 2000) if custom_settings else 2000
        temperature = float(custom_settings.get('temperature', 0.7)) if custom_settings else 0.7
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                print(f"💬 Отправляем сообщение в чат: {message[:50]}...")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=120.0  # Увеличиваем таймаут для долгих ответов
                )
                response.raise_for_status()
                
                result = response.json()
                if "choices" not in result or len(result["choices"]) == 0:
                    raise ValueError("Пустой ответ от API")
                content = result["choices"][0]["message"]["content"]
                print(f"✅ Получен ответ от LLM: {content[:100]}...")
                return content
                
            except httpx.HTTPStatusError as e:
                print(f"Ошибка HTTP запроса к Polza.AI для чата: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Статус код: {e.response.status_code}")
                    try:
                        error_data = e.response.json()
                        error_msg = error_data.get("error", {}).get("message", str(e))
                    except:
                        error_msg = e.response.text[:200]
                    print(f"Ответ: {error_msg}")
                return f"Извините, произошла ошибка при обращении к AI (HTTP {e.response.status_code if hasattr(e, 'response') else 'unknown'}). Попробуйте переформулировать запрос или повторить позже."
            except httpx.TimeoutException as e:
                print(f"Таймаут при обращении к Polza.AI для чата: {e}")
                return "Извините, запрос к AI занял слишком много времени. Попробуйте упростить запрос или повторить позже."
            except Exception as e:
                print(f"Ошибка при общении с LLM: {e}")
                import traceback
                traceback.print_exc()
                return f"Извините, произошла ошибка при общении с AI: {str(e)[:100]}. Попробуйте переформулировать запрос."
    
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
