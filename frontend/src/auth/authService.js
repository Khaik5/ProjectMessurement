import axiosClient from '../api/axiosClient.js';
import { unwrapApi } from '../services/apiUtils.js';

export const authService = {
  login: (payload) => axiosClient.post('/auth/login', payload).then(unwrapApi),
  logout: () => axiosClient.post('/auth/logout').then(unwrapApi),
  me: () => axiosClient.get('/auth/me').then(unwrapApi),
  register: (payload) => axiosClient.post('/auth/register', payload).then(unwrapApi),
  publicRegister: (payload) => axiosClient.post('/auth/public-register', payload).then(unwrapApi),
  users: () => axiosClient.get('/auth/users').then(unwrapApi),
  roles: () => axiosClient.get('/auth/roles').then(unwrapApi),
  updateUser: (id, payload) => axiosClient.put(`/auth/users/${id}`, payload).then(unwrapApi),
  updateUserRole: (id, role) => axiosClient.patch(`/auth/users/${id}/role`, { role }).then(unwrapApi),
  deleteUser: (id) => axiosClient.delete(`/auth/users/${id}`).then(unwrapApi)
};

