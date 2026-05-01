import axiosClient from "../api/axiosClient";
import { unwrapApi } from "./apiUtils";

export const checkBackendHealth = () => {
  return axiosClient.get("/health").then(unwrapApi);
};
