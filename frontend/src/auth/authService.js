import axiosClient from '../api/axiosClient.js';

export const authService = {
  login: (payload) => axiosClient.post('/auth/login', payload).then((res) => res.data),
  logout: () => axiosClient.post('/auth/logout').then((res) => res.data),
  me: () => axiosClient.get('/auth/me').then((res) => res.data),
  register: (payload) => axiosClient.post('/auth/register', payload).then((res) => res.data),
  users: () => axiosClient.get('/auth/users').then((res) => res.data),
  roles: () => axiosClient.get('/auth/roles').then((res) => res.data),
  updateUser: (id, payload) => axiosClient.put(`/auth/users/${id}`, payload).then((res) => res.data),
  deleteUser: (id) => axiosClient.delete(`/auth/users/${id}`).then((res) => res.data)
};

