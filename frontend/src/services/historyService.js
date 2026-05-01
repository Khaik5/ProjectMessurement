import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from './apiUtils.js';

export const historyService = {
  list: (projectId = 1) => axiosClient.get('/history', { params: { project_id: projectId } }).then(unwrapApi),
  get: (datasetId) => axiosClient.get(`/history/${datasetId}`).then(unwrapApi),
  setCurrent: (datasetId) => axiosClient.post(`/history/${datasetId}/set-current`).then(unwrapApi),
  reanalyze: (datasetId, projectId = 1, modelId = null) =>
    axiosClient.post(`/history/${datasetId}/reanalyze`, null, { params: { project_id: projectId, model_id: modelId }, timeout: 300000 }).then(unwrapApi),
  archive: (datasetId) => axiosClient.delete(`/history/${datasetId}`).then(unwrapApi)
};

