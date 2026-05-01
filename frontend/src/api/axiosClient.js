import axios from "axios";

import { getToken } from "../auth/tokenStorage.js";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
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
    const isTimeout = error.code === "ECONNABORTED";
    const networkMessage =
      error.message === "Network Error"
        ? `Cannot reach backend API at ${API_BASE_URL}.`
        : isTimeout
          ? "The backend is taking longer than expected."
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
      window.dispatchEvent(new CustomEvent("defectai:toast", { detail: { message: "You do not have permission for this action.", type: "error" } }));
    }

    return Promise.reject({
      status: error.response?.status || 0,
      message,
      raw: error.response?.data || null,
    });
  }
);

export default axiosClient;
