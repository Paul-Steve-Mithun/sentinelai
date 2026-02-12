import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Employees
export const getEmployees = () => api.get('/api/employees');
export const getEmployee = (id) => api.get(`/api/employees/${id}`);
export const createEmployee = (data) => api.post('/api/employees', data);
export const getEmployeeProfile = (id) => api.get(`/api/employees/${id}/profile`);
export const getEmployeeAnomalies = (id) => api.get(`/api/employees/${id}/anomalies`);

// Events
export const createEvent = (data) => api.post('/api/events', data);
export const getEmployeeEvents = (id) => api.get(`/api/events/${id}`);

// Anomalies
export const getAnomalies = (params) => api.get('/api/anomalies', { params });
export const getAnomaly = (id) => api.get(`/api/anomalies/${id}`);
export const getAnomalyMitre = (id) => api.get(`/api/anomalies/${id}/mitre`);
export const getAnomalyMitigation = (id) => api.get(`/api/anomalies/${id}/mitigation`);
export const resolveAnomaly = (id, data) => api.post(`/api/anomalies/${id}/resolve`, data);
export const implementMitigation = (anomalyId, strategyId, data) =>
    api.post(`/api/anomalies/${anomalyId}/mitigation/${strategyId}/implement`, data);

// Dashboard
export const getDashboardStats = () => api.get('/api/dashboard/stats');
export const getRiskDistribution = () => api.get('/api/dashboard/risk-distribution');
export const getTopThreats = () => api.get('/api/dashboard/top-threats');
export const getAnomalyTimeline = (days = 30) => api.get(`/api/dashboard/timeline?days=${days}`);

// ML Operations
export const trainModel = () => api.post('/api/ml/train');
export const getModelInfo = () => api.get('/api/ml/model-info');
export const predict = (data) => api.post('/api/ml/predict', data);

export default api;
