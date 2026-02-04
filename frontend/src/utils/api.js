import axios from 'axios';

//const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
//const API_URL = 'https://llm-prompts-backend.onrender.com/api';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://llm-prompts-backend.onrender.com/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const promptsAPI = {
  // Get all prompts with optional filters
  getPrompts: async (params = {}) => {
    const response = await api.get('/prompts', { params });
    return response.data;
  },

  // Get a single prompt by ID
  getPrompt: async (id) => {
    const response = await api.get(`/prompts/${id}`);
    return response.data;
  },

  // Create a new prompt
  createPrompt: async (promptData) => {
    const response = await api.post('/prompts', promptData);
    return response.data;
  },

  // Get all categories
  getCategories: async () => {
    const response = await api.get('/categories');
    return response.data;
  },

  // Get statistics
  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },
};

export default api;
