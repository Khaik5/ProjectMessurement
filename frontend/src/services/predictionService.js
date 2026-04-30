import axiosClient from '../api/axiosClient.js';

export const getDatasetPredictions = (datasetId) =>
  axiosClient.get(`/predictions/dataset/${datasetId}`);

export const runDatasetAnalysis = (payload) =>
  axiosClient.post('/predictions/run', payload);

export const predictionService = {
  run: (payload) => runDatasetAnalysis(payload).then((res) => res.data),
  single: (payload) => axiosClient.post('/predictions/single', payload).then((res) => res.data),
  list: () => axiosClient.get('/predictions').then((res) => res.data),
  byProject: (projectId) => axiosClient.get(`/predictions/project/${projectId}`).then((res) => res.data),
  byDataset: (datasetId) => getDatasetPredictions(datasetId).then((res) => res.data),
  topRisk: (projectId = 1) => axiosClient.get('/predictions/top-risk', { params: { project_id: projectId } }).then((res) => res.data),
  recent: () => axiosClient.get('/predictions/recent').then((res) => res.data)
};
