import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';

// WAŻNE: localhost często nie działa. Zmień na IP swojego komputera w sieci lokalnej
const API_URL = 'http://192.168.1.8:8000';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor żądań (Request)
apiClient.interceptors.request.use(
    (config) => {
        // Pobieramy token w locie z Zustanda
        const token = useAuthStore.getState().token;

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);