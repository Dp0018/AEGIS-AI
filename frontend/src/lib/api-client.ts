import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request Interceptor: Attach Access Token
apiClient.interceptors.request.use((config) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token && config.headers && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response Interceptor: Auto-Refresh Access Tokens on 401 Unauthorized
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        if (
            error.response?.status === 401 &&
            !originalRequest._retry &&
            originalRequest.url !== "/auth/refresh" &&
            originalRequest.url !== "/auth/token"
        ) {
            originalRequest._retry = true;
            const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
            
            if (refreshToken) {
                try {
                    const refreshRes = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });
                    
                    const { access_token, refresh_token } = refreshRes.data;
                    localStorage.setItem("access_token", access_token);
                    localStorage.setItem("refresh_token", refresh_token);
                    
                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return apiClient(originalRequest);
                } catch (refreshErr) {
                    // Token invalid/expired, logout user
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");
                    localStorage.removeItem("user_email");
                    localStorage.removeItem("user_name");
                    if (typeof window !== "undefined") {
                        window.location.href = "/login";
                    }
                    return Promise.reject(refreshErr);
                }
            }
        }
        
        // Extract readable server error details
        const errMsg = error.response?.data?.detail || error.response?.data?.message || error.message;
        return Promise.reject(new Error(errMsg));
    }
);

export default apiClient;
export { apiClient };
