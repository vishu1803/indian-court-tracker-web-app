// frontend/src/lib/api.js
import axios from 'axios';
import toast from 'react-hot-toast';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds timeout for scraping operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed in future
    // config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || 'An error occurred';
      toast.error(message);
    } else if (error.request) {
      // Request made but no response received
      toast.error('Unable to connect to server. Please check your connection.');
    } else {
      // Something else happened
      toast.error('An unexpected error occurred');
    }
    
    return Promise.reject(error);
  }
);

// API endpoints
export const apiEndpoints = {
  // Case search
  searchCase: (caseData) => api.post('/api/v1/cases/search', caseData),
  getCaseById: (queryId) => api.get(`/api/v1/cases/${queryId}`),
  refreshCase: (queryId) => api.post(`/api/v1/cases/${queryId}/refresh`),
  getRecentSearches: (limit = 20) => api.get(`/api/v1/cases/recent?limit=${limit}`),
  
  // Cause lists
  getCauseListByDate: (dateData) => api.post('/api/v1/cause-lists/by-date', dateData),
  checkCaseInCauseList: (params) => api.get('/api/v1/cause-lists/check-case', { params }),
  getAvailableCourts: () => api.get('/api/v1/cause-lists/courts'),
  getCauseListStats: (params) => api.get('/api/v1/cause-lists/stats', { params }),
  
  // Judgments
  downloadJudgment: (judgmentId) => api.get(`/api/v1/judgments/download/${judgmentId}`, {
    responseType: 'blob'
  }),
  
  // Health check
  healthCheck: () => api.get('/health'),
};

// Helper functions
export const downloadFile = async (judgmentId, filename) => {
  try {
    const response = await apiEndpoints.downloadJudgment(judgmentId);
    
    // Create blob link to download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename || `judgment_${judgmentId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    toast.success('File downloaded successfully');
  } catch (error) {
    console.error('Download error:', error);
    toast.error('Failed to download file');
  }
};

export default api;
