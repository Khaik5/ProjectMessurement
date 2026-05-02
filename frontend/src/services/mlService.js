import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from './apiUtils.js';

export const getModels = (projectId = 1) =>
  axiosClient.get(`/ml/models?project_id=${projectId}`);

export const getTrainingRuns = (projectId = 1) =>
  axiosClient.get(`/ml/training-runs?project_id=${projectId}`);

export const trainProductionModel = (payload) =>
  axiosClient.post('/ml/train-production', payload, { timeout: 300000 });

export const mlService = {
  train: (payload) => axiosClient.post('/ml/train', payload, { timeout: 300000 }).then(unwrapApi),
  trainProduction: (payload) => trainProductionModel(payload).then(unwrapApi),
  models: (projectId = 1) => getModels(projectId).then(unwrapApi),
  model: (id) => axiosClient.get(`/ml/models/${id}`).then(unwrapApi),
  activate: (id) => axiosClient.put(`/ml/models/${id}/activate`).then(unwrapApi),
  deleteModel: (id) => axiosClient.delete(`/ml/models/${id}`).then(unwrapApi),
  trainingRuns: (projectId = 1) => getTrainingRuns(projectId).then(unwrapApi),
  trainingRun: (id) => axiosClient.get(`/ml/training-runs/${id}`).then(unwrapApi),
  deleteTrainingRun: (id) => axiosClient.delete(`/ml/training-runs/${id}`).then(unwrapApi),
  restoreTrainingRun: (id) => axiosClient.post(`/ml/training-runs/${id}/restore`).then(unwrapApi),
  comparison: (projectId = 1, datasetId = null) => axiosClient.get('/ml/model-comparison', { params: { project_id: projectId, dataset_id: datasetId } }).then(unwrapApi),
  trainableDatasets: (projectId = 1) => axiosClient.get('/ml/trainable-datasets', { params: { project_id: projectId } }).then(unwrapApi),
  trainingGuide: () => axiosClient.get('/ml/training-guide').then(unwrapApi)
};
