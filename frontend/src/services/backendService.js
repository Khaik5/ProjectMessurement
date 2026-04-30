import axiosClient from "../api/axiosClient";

export const checkBackendHealth = () => {
  return axiosClient.get("/health");
};
