import axios from 'axios';

// Определяем базовый URL API
// На сервере всегда используем /api через nginx
// Для локальной разработки можно установить REACT_APP_API_URL=http://localhost:8001
const getApiBaseUrl = () => {
  const envUrl = process.env.REACT_APP_API_URL;
  
  // Если переменная окружения не установлена или пустая - используем /api (через nginx)
  if (!envUrl || envUrl.trim() === '') {
    return '/api';
  }
  
  // Если установлена переменная с портом (для локальной разработки)
  if (envUrl.includes(':8000') || envUrl.includes(':8001')) {
    return envUrl;
  }
  
  // По умолчанию используем /api
  return '/api';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 минуты для долгих запросов к AI
});

// Перехватчик для обработки ошибок
api.interceptors.response.use(
  (response) => {
    // Успешный ответ - просто возвращаем его
    return response;
  },
  (error) => {
    // Обработка ошибок
    console.error('API Error:', error);
    
    if (error.response) {
      // Сервер ответил с кодом ошибки
      const status = error.response.status;
      const data = error.response.data;
      
      console.error(`API Error ${status}:`, data);
      
      // Возвращаем ошибку с понятным сообщением
      const errorMessage = data?.detail || data?.message || `Ошибка сервера: ${status}`;
      return Promise.reject(new Error(errorMessage));
    } else if (error.request) {
      // Запрос был отправлен, но ответа не получено
      console.error('Network Error:', error.request);
      return Promise.reject(new Error('Нет соединения с сервером. Проверьте подключение к интернету.'));
    } else {
      // Что-то пошло не так при настройке запроса
      console.error('Request Error:', error.message);
      return Promise.reject(new Error(`Ошибка запроса: ${error.message}`));
    }
  }
);

export const companyService = {
  // Получить список компаний
  getCompanies: async (skip = 0, limit = 100) => {
    const response = await api.get(`/companies?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Получить информацию о компании
  getCompany: async (id) => {
    const response = await api.get(`/companies/${id}`);
    return response.data;
  },

  // Обновить информацию о компании
  updateCompany: async (id, data) => {
    const response = await api.put(`/companies/${id}`, data);
    return response.data;
  },

  // Поиск информации о компании
  searchCompany: async (companyName) => {
    const response = await api.post('/companies/search', { query: companyName });
    return response.data;
  },

  // Создать новую компанию
  createCompany: async (companyData) => {
    const response = await api.post('/companies', companyData);
    return response.data;
  },

  // Массовый поиск компаний из файла
  bulkSearchCompanies: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/companies/bulk-search', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const equipmentService = {
  // Получить список оборудования
  getEquipment: async (skip = 0, limit = 100) => {
    const response = await api.get(`/equipment?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Поиск компаний по оборудованию
  searchCompaniesByEquipment: async (equipmentName) => {
    const response = await api.post('/equipment/search', { query: equipmentName });
    return response.data;
  },
};

export const searchLogService = {
  // Получить историю поисков
  getSearchLogs: async (skip = 0, limit = 100) => {
    const response = await api.get(`/search-logs?skip=${skip}&limit=${limit}`);
    return response.data;
  },
};

export const chatService = {
  // Отправить сообщение в диалог
  sendDialogMessage: async (message, dialogId, conversationHistory) => {
    const response = await api.post('/chat/dialog', {
      message,
      dialog_id: dialogId,
      conversation_history: conversationHistory || []
    });
    return response.data;
  },
};

export const dialogService = {
  // Получить список диалогов
  getDialogs: async (skip = 0, limit = 100) => {
    const response = await api.get(`/dialogs?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Получить диалог по ID
  getDialog: async (dialogId) => {
    const response = await api.get(`/dialogs/${dialogId}`);
    return response.data;
  },

  // Создать новый диалог
  createDialog: async (title) => {
    const response = await api.post('/dialogs', { title });
    return response.data;
  },

  // Удалить диалог
  deleteDialog: async (dialogId) => {
    const response = await api.delete(`/dialogs/${dialogId}`);
    return response.data;
  },
};

export const settingsService = {
  // Получить список помощников
  getAssistants: async (skip = 0, limit = 100) => {
    const response = await api.get(`/assistants?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Получить список моделей
  getModels: async () => {
    const response = await api.get('/models');
    return response.data;
  },

  // Получить настройки диалога
  getDialogSettings: async (dialogId) => {
    const response = await api.get(`/dialogs/${dialogId}/settings`);
    return response.data;
  },

  // Обновить настройки диалога
  updateDialogSettings: async (dialogId, settings) => {
    const response = await api.put(`/dialogs/${dialogId}/settings`, settings);
    return response.data;
  },

  // Получить файлы диалога
  getDialogFiles: async (dialogId) => {
    const response = await api.get(`/dialogs/${dialogId}/files`);
    return response.data;
  },

  // Удалить файл диалога
  deleteDialogFile: async (dialogId, fileId) => {
    const response = await api.delete(`/dialogs/${dialogId}/files/${fileId}`);
    return response.data;
  },

  // Создать помощника
  createAssistant: async (assistantData) => {
    const response = await api.post('/assistants', assistantData);
    return response.data;
  },

  // Обновить помощника
  updateAssistant: async (assistantId, assistantData) => {
    const response = await api.put(`/assistants/${assistantId}`, assistantData);
    return response.data;
  },

  // Удалить помощника
  deleteAssistant: async (assistantId) => {
    const response = await api.delete(`/assistants/${assistantId}`);
    return response.data;
  },
};

export const emailService = {
  // Проверить email адрес
  verifyEmail: async (email, companyId = null) => {
    const response = await api.post('/email/verify', { email, company_id: companyId });
    return response.data;
  },

  // Создать email рассылку
  createCampaign: async (campaignData) => {
    const response = await api.post('/email/campaign', campaignData);
    return response.data;
  },

  // Отправить email рассылку
  sendCampaign: async (campaignId) => {
    const response = await api.post(`/email/campaign/${campaignId}/send`);
    return response.data;
  },

  // Получить список рассылок
  getCampaigns: async (skip = 0, limit = 100) => {
    const response = await api.get(`/email/campaigns?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Получить список проверок email
  getVerifications: async (skip = 0, limit = 100) => {
    const response = await api.get(`/email/verifications?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Массовая проверка всех email
  bulkVerifyEmails: async () => {
    const response = await api.post('/companies/bulk-verify-emails');
    return response.data;
  },
};

export const agentService = {
  // Выполнить действие агента
  performAction: async (action, parameters) => {
    const response = await api.post('/agent/action', {
      action,
      parameters
    });
    return response.data;
  },
};

export default api;
