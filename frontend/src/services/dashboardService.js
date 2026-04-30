import axiosClient from '../api/axiosClient.js';

export const getDashboardSummary = (projectId, datasetId) =>
  axiosClient.get(`/dashboard/summary?project_id=${projectId}&dataset_id=${datasetId}`);

export const getDashboardCharts = (projectId, datasetId) =>
  axiosClient.get(`/dashboard/charts?project_id=${projectId}&dataset_id=${datasetId}`);

export const dashboardService = {
  summary: (projectId = 1, datasetId) =>
    datasetId
      ? getDashboardSummary(projectId, datasetId).then((res) => res.data)
      : axiosClient.get('/dashboard/summary', { params: { project_id: projectId } }).then((res) => res.data),
  charts: (projectId = 1, datasetId) =>
    datasetId
      ? getDashboardCharts(projectId, datasetId).then((res) => res.data)
      : axiosClient.get('/dashboard/charts', { params: { project_id: projectId } }).then((res) => res.data)
};
