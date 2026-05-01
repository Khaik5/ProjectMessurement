import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from './apiUtils.js';

export const projectService = {
  list: () => axiosClient.get('/projects').then(unwrapApi),
  get: (id) => axiosClient.get(`/projects/${id}`).then(unwrapApi),
  state: (id) => axiosClient.get(`/projects/${id}/state`).then(unwrapApi),
  updateState: (id, payload) => axiosClient.put(`/projects/${id}/state`, payload).then(unwrapApi),
  create: (payload) => axiosClient.post('/projects', payload).then(unwrapApi),
  update: (id, payload) => axiosClient.put(`/projects/${id}`, payload).then(unwrapApi),
  remove: (id) => axiosClient.delete(`/projects/${id}`).then(unwrapApi)
};
