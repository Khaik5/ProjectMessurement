import axiosClient from '../api/axiosClient.js';

export const getModels = (projectId = 1) =>
  axiosClient.get(`/ml/models?project_id=${projectId}`);

export const getTrainingRuns = (projectId = 1) =>
  axiosClient.get(`/ml/training-runs?project_id=${projectId}`);

export const trainProductionModel = (payload) =>
  axiosClient.post('/ml/train-production', payload);

export const mlService = {
  train: (payload) => axiosClient.post('/ml/train', payload).then((res) => res.data?.data || res.data),
  trainProduction: (payload) => trainProductionModel(payload).then((res) => res.data?.data || res.data),
  models: (projectId = 1) => getModels(projectId).then((res) => res.data?.data || res.data),
  model: (id) => axiosClient.get(`/ml/models/${id}`).then((res) => res.data?.data || res.data),
  activate: (id) => axiosClient.put(`/ml/models/${id}/activate`).then((res) => res.data?.data || res.data),
  deleteModel: (id) => axiosClient.delete(`/ml/models/${id}`).then((res) => res.data?.data || res.data),
  trainingRuns: (projectId = 1) => getTrainingRuns(projectId).then((res) => res.data?.data || res.data),
  trainingRun: (id) => axiosClient.get(`/ml/training-runs/${id}`).then((res) => res.data?.data || res.data),
  deleteTrainingRun: (id) => axiosClient.delete(`/ml/training-runs/${id}`).then((res) => res.data?.data || res.data),
  restoreTrainingRun: (id) => axiosClient.post(`/ml/training-runs/${id}/restore`).then((res) => res.data?.data || res.data),
  comparison: (projectId = 1) => axiosClient.get('/ml/comparison', { params: { project_id: projectId } }).then((res) => res.data?.data || res.data),
  trainableDatasets: (projectId = 1) => axiosClient.get('/ml/trainable-datasets', { params: { project_id: projectId } }).then((res) => res.data?.data || res.data),
  trainingGuide: () => axiosClient.get('/ml/training-guide').then((res) => res.data?.data || res.data)
};
