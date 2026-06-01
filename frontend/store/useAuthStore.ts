import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

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
            await SecureStore.setItemAsync(TOKEN_KEY, token);
        } else {
            await SecureStore.deleteItemAsync(TOKEN_KEY);
        }
        set({ token });
    },

    logout: async () => {
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        set({ token: null });
    },
    loadToken: async () => {
        try {
            const token = await SecureStore.getItemAsync(TOKEN_KEY);
            set({ token, isLoading: false });
        } catch (error) {
            set({ token: null, isLoading: false });
        }
    }
}));