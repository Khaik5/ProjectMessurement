import axios from "axios";

import { getToken } from "../auth/tokenStorage.js";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

axiosClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosClient.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === "object") {
      return response.data;
    }
    return response;
  },
  (error) => {
    const networkMessage =
      error.message === "Network Error"
        ? `Cannot reach backend API at ${API_BASE_URL}. Check uvicorn, SQL Server connection, and CORS.`
        : error.message;
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      networkMessage ||
      "Cannot reach backend API";

    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent("defectai:logout"));
    }
    if (error.response?.status === 403) {
      window.dispatchEvent(new CustomEvent("defectai:toast", { detail: { message: "Bạn không có quyền thực hiện chức năng này.", type: "error" } }));
    }

    return Promise.reject({
      status: error.response?.status || 0,
      message,
      raw: error.response?.data || null,
    });
  }
);

export default axiosClient;
