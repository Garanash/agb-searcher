import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  // Отправить сообщение в чат (legacy)
  sendMessage: async (message, conversationHistory = []) => {
    const response = await api.post('/chat', {
      message,
      conversation_history: conversationHistory
    });
    return response.data;
  },

  // Отправить сообщение в диалог
  sendDialogMessage: async (message, dialogId = null, conversationHistory = []) => {
    const response = await api.post('/chat/dialog', {
      message,
      dialog_id: dialogId,
      conversation_history: conversationHistory
    });
    return response.data;
  },
};

export const dialogService = {
  // Создать новый диалог
  createDialog: async (title) => {
    const response = await api.post('/dialogs', { title });
    return response.data;
  },

  // Получить список диалогов
  getDialogs: async (skip = 0, limit = 100) => {
    const response = await api.get(`/dialogs?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Получить диалог с сообщениями
  getDialog: async (dialogId) => {
    const response = await api.get(`/dialogs/${dialogId}`);
    return response.data;
  },

  // Обновить диалог
  updateDialog: async (dialogId, updates) => {
    const response = await api.put(`/dialogs/${dialogId}`, updates);
    return response.data;
  },

  // Удалить диалог
  deleteDialog: async (dialogId) => {
    const response = await api.delete(`/dialogs/${dialogId}`);
    return response.data;
  },
};

export const settingsService = {
  // Настройки диалогов
  createDialogSettings: async (dialogId, settings) => {
    const response = await api.post(`/dialogs/${dialogId}/settings`, settings);
    return response.data;
  },

  getDialogSettings: async (dialogId) => {
    const response = await api.get(`/dialogs/${dialogId}/settings`);
    return response.data;
  },

  updateDialogSettings: async (dialogId, settings) => {
    const response = await api.put(`/dialogs/${dialogId}/settings`, settings);
    return response.data;
  },

  // Файлы диалогов
  uploadDialogFile: async (dialogId, formData) => {
    const response = await api.post(`/dialogs/${dialogId}/files`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getDialogFiles: async (dialogId) => {
    const response = await api.get(`/dialogs/${dialogId}/files`);
    return response.data;
  },

  deleteDialogFile: async (dialogId, fileId) => {
    const response = await api.delete(`/dialogs/${dialogId}/files/${fileId}`);
    return response.data;
  },

  // Помощники
  createAssistant: async (assistant) => {
    const response = await api.post('/assistants', assistant);
    return response.data;
  },

  getAssistants: async (skip = 0, limit = 100) => {
    const response = await api.get(`/assistants?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getAssistant: async (assistantId) => {
    const response = await api.get(`/assistants/${assistantId}`);
    return response.data;
  },

  updateAssistant: async (assistantId, updates) => {
    const response = await api.put(`/assistants/${assistantId}`, updates);
    return response.data;
  },

  deleteAssistant: async (assistantId) => {
    const response = await api.delete(`/assistants/${assistantId}`);
    return response.data;
  },

  // Модели
  getModels: async () => {
    const response = await api.get('/models');
    return response.data;
  },
};

export default api;
