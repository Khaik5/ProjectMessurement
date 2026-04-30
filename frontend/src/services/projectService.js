import axiosClient from '../api/axiosClient.js';

export const projectService = {
  list: () => axiosClient.get('/projects').then((res) => res.data),
  get: (id) => axiosClient.get(`/projects/${id}`).then((res) => res.data),
  state: (id) => axiosClient.get(`/projects/${id}/state`).then((res) => res.data),
  updateState: (id, payload) => axiosClient.put(`/projects/${id}/state`, payload).then((res) => res.data),
  create: (payload) => axiosClient.post('/projects', payload).then((res) => res.data),
  update: (id, payload) => axiosClient.put(`/projects/${id}`, payload).then((res) => res.data),
  remove: (id) => axiosClient.delete(`/projects/${id}`).then((res) => res.data)
};
