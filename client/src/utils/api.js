import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// Add request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API] Response: ${response.status}`);
    return response;
  },
  (error) => {
    let errorMessage = "An error occurred";

    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      if (status === 429) {
        errorMessage = "Too many requests. Please wait before trying again.";
      } else if (status === 422) {
        errorMessage = "Invalid input. Please check your text.";
      } else if (status >= 500) {
        errorMessage = "Server error. Please try again later.";
      } else {
        errorMessage = error.response.data?.detail || `Error: ${status}`;
      }
    } else if (error.request) {
      // Request was made but no response received
      errorMessage =
        "Connection failed. Is the backend server running on localhost:8000?";
    } else {
      errorMessage = error.message;
    }

    console.error(`[API] Error: ${errorMessage}`);
    return Promise.reject({ message: errorMessage, originalError: error });
  }
);

export const analyzeText = async (text) => {
  try {
    const response = await apiClient.post("/analyze", { text });
    return response.data;
  } catch (error) {
    throw error.message || error;
  }
};

export const healthCheck = async () => {
  try {
    const response = await apiClient.get("/health");
    return response.data;
  } catch (error) {
    throw error;
  }
};

export default apiClient;
