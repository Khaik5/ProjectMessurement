import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from './apiUtils.js';

export const getDashboardSummary = (projectId, datasetId) =>
  axiosClient.get(`/dashboard/summary?project_id=${projectId}&dataset_id=${datasetId}`);

export const getDashboardCharts = (projectId, datasetId) =>
  axiosClient.get(`/dashboard/charts?project_id=${projectId}&dataset_id=${datasetId}`);

export const dashboardService = {
  summary: (projectId = 1, datasetId) =>
    datasetId
      ? getDashboardSummary(projectId, datasetId).then(unwrapApi)
      : axiosClient.get('/dashboard/summary', { params: { project_id: projectId } }).then(unwrapApi),
  charts: (projectId = 1, datasetId) =>
    datasetId
      ? getDashboardCharts(projectId, datasetId).then(unwrapApi)
      : axiosClient.get('/dashboard/charts', { params: { project_id: projectId } }).then(unwrapApi)
};
