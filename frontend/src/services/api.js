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

export default api;
