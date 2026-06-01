import { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { Slot, useRouter, useSegments } from 'expo-router';
import { useAuthStore } from '@/store/useAuthStore';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

export default function RootLayout() {
  const { token, isLoading, loadToken } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    loadToken();
    setIsReady(true);
  }, []);

  useEffect(() => {
    if (!isReady || isLoading) return;

    const isLoginScreen = segments[0] === 'login';
    const isRegisterScreen = segments[0] === 'register';

    setTimeout(() => {
      if (!token && !isLoginScreen && !isRegisterScreen) {
        router.replace('/login' as any);
      } else if (token && (isLoginScreen || isRegisterScreen)) {
        router.replace('/(tabs)' as any);
      }
    }, 0);

  }, [token, segments, isReady, isLoading]);

  if (isLoading) {
    return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#2980b9" />
        </View>
    );
  }

  return (
      <QueryClientProvider client={queryClient}>
        <Slot />
      </QueryClientProvider>
  );
}
