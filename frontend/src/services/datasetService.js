import axiosClient from '../api/axiosClient.js';

export const getDatasetHistory = (projectId = 1) =>
  axiosClient.get(`/datasets/history?project_id=${projectId}`);

export const getDatasetPreview = (datasetId) =>
  axiosClient.get(`/datasets/${datasetId}/preview`);

export const uploadDataset = (formData) =>
  axiosClient.post('/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

export const exportDatasetXlsx = (datasetId) =>
  axiosClient.get(`/datasets/${datasetId}/export/xlsx`, {
    responseType: 'blob'
  });

export const exportDataset = (datasetId, type) =>
  axiosClient.get(`/datasets/${datasetId}/export/${type}`, {
    responseType: 'blob'
  });

export const datasetService = {
  list: () => axiosClient.get('/datasets').then((res) => res.data),
  history: (projectId = 1) => getDatasetHistory(projectId).then((res) => res.data),
  get: (id) => axiosClient.get(`/datasets/${id}`).then((res) => res.data),
  preview: (id) => getDatasetPreview(id).then((res) => res.data),
  upload: (file, projectId = 1) => {
    const form = new FormData();
    form.append('project_id', projectId);
    form.append('file', file);
    return uploadDataset(form).then((res) => res.data);
  },
  remove: (id) => axiosClient.delete(`/datasets/${id}`).then((res) => res.data),
  setCurrent: (id) => axiosClient.post(`/datasets/${id}/set-current`).then((res) => res.data),
  analysisSummary: (id) => axiosClient.get(`/datasets/${id}/analysis-summary`).then((res) => res.data),
  export: (id, type) => exportDataset(id, type),
  exportUrl: (id, type) => `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/datasets/${id}/export/${type}`
};
