import { create } from 'zustand';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const isWeb = Platform.OS === 'web';

const storage = {
    async setItem(key: string, value: string): Promise<void> {
        if (isWeb) {
            window.localStorage.setItem(key, value);
        } else {
            await SecureStore.setItemAsync(key, value);
        }
    },
    async getItem(key: string): Promise<string | null> {
        if (isWeb) {
            return window.localStorage.getItem(key);
        }
        return SecureStore.getItemAsync(key);
    },
    async deleteItem(key: string): Promise<void> {
        if (isWeb) {
            window.localStorage.removeItem(key);
        } else {
            await SecureStore.deleteItemAsync(key);
        }
    },
};

interface AuthState {
    token: string | null;
    isLoading: boolean;
    setToken: (token: string | null) => Promise<void>;
    logout: () => Promise<void>;
    loadToken: () => Promise<void>;
}

const TOKEN_KEY = 'smart_pot_jwt';

export const useAuthStore = create<AuthState>((set) => ({
    token: null,
    isLoading: true,

    setToken: async (token) => {
        if (token) {
            await storage.setItem(TOKEN_KEY, token);
        } else {
            await storage.deleteItem(TOKEN_KEY);
        }
        set({ token });
    },

    logout: async () => {
        await storage.deleteItem(TOKEN_KEY);
        set({ token: null });
    },
    loadToken: async () => {
        try {
            const token = await storage.getItem(TOKEN_KEY);
            set({ token, isLoading: false });
        } catch (error) {
            set({ token: null, isLoading: false });
        }
    }
}));