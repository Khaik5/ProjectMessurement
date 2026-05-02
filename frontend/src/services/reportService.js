import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from './apiUtils.js';

export const reportService = {
  list: (projectId = 1) => axiosClient.get(`/reports?project_id=${projectId}`).then(unwrapApi),
  get: (id) => axiosClient.get(`/reports/${id}`).then(unwrapApi),
  generate: (payload) => axiosClient.post('/reports/generate', payload).then(unwrapApi),
  remove: (id) => axiosClient.delete(`/reports/${id}`).then(unwrapApi),
  exportReport: (id, type) => axiosClient.get(`/reports/${id}/export/${type}`, { responseType: 'blob' }),
  exportDataset: (datasetId, type, options = {}) => {
    const endpointType = type === 'xlsx' ? 'excel' : type;
    const params = new URLSearchParams({
      dataset_id: String(datasetId),
      include_full_modules: String(options.include_full_modules ?? true),
      include_heatmap: String(options.include_heatmap ?? true),
      include_charts: String(options.include_charts ?? true),
      top_n: String(options.top_n ?? 20)
    });
    if (endpointType === 'csv') {
      return axiosClient.get(`/reports/dataset/${datasetId}/export/csv`, { responseType: 'blob' });
    }
    return axiosClient.get(`/reports/export/${endpointType}?${params.toString()}`, { responseType: 'blob' });
  },
  exportUrl: (id, type) => `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/reports/${id}/export/${type}`
};
