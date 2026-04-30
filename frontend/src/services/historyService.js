import axiosClient from '../api/axiosClient.js';

export const historyService = {
  list: (projectId = 1) => axiosClient.get('/history', { params: { project_id: projectId } }).then((res) => res.data),
  get: (datasetId) => axiosClient.get(`/history/${datasetId}`).then((res) => res.data),
  setCurrent: (datasetId) => axiosClient.post(`/history/${datasetId}/set-current`).then((res) => res.data),
  reanalyze: (datasetId, projectId = 1, modelId = null) =>
    axiosClient.post(`/history/${datasetId}/reanalyze`, null, { params: { project_id: projectId, model_id: modelId } }).then((res) => res.data),
  archive: (datasetId) => axiosClient.delete(`/history/${datasetId}`).then((res) => res.data)
};

