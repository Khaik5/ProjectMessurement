import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from './apiUtils.js';

export const getDatasetPredictions = (datasetId) =>
  axiosClient.get(`/predictions/dataset/${datasetId}`);

export const runDatasetAnalysis = (payload) =>
  axiosClient.post('/predictions/run', payload);

export const predictionService = {
  run: (payload) => runDatasetAnalysis(payload).then(unwrapApi),
  single: (payload) => axiosClient.post('/predictions/single', payload).then(unwrapApi),
  list: () => axiosClient.get('/predictions').then(unwrapApi),
  byProject: (projectId) => axiosClient.get(`/predictions/project/${projectId}`).then(unwrapApi),
  byDataset: (datasetId) => getDatasetPredictions(datasetId).then(unwrapApi),
  topRisk: (projectId = 1) => axiosClient.get('/predictions/top-risk', { params: { project_id: projectId } }).then(unwrapApi),
  recent: () => axiosClient.get('/predictions/recent').then(unwrapApi)
};
