import axiosClient from '../api/axiosClient.js';

export const reportService = {
  list: (projectId = 1) => axiosClient.get(`/reports?project_id=${projectId}`).then((res) => res.data),
  get: (id) => axiosClient.get(`/reports/${id}`).then((res) => res.data),
  generate: (payload) => axiosClient.post('/reports/generate', payload).then((res) => res.data),
  remove: (id) => axiosClient.delete(`/reports/${id}`).then((res) => res.data),
  exportReport: (id, type) => axiosClient.get(`/reports/${id}/export/${type}`, { responseType: 'blob' }),
  exportDataset: (datasetId, type) => axiosClient.get(`/reports/dataset/${datasetId}/export/${type}`, { responseType: 'blob' }),
  exportUrl: (id, type) => `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/reports/${id}/export/${type}`
};
