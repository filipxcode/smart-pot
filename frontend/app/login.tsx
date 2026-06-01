import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useAuthStore } from '@/store/useAuthStore';
import { apiClient } from '@/api/client';
import { Link } from 'expo-router';

export default function LoginScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const setToken = useAuthStore((state) => state.setToken);

    const handleLogin = async () => {
        if (!email || !password) {
            Alert.alert('Błąd', 'Wpisz email i hasło');
            return;
        }

        setLoading(true);
        try {
            // FastAPI wymaga formatu x-www-form-urlencoded do logowania OAuth2
            const params = new URLSearchParams();
            params.append('username', email); // fastapi-users oczekuje klucza "username"
            params.append('password', password);

            const response = await apiClient.post('/auth/jwt/login', params.toString(), {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            // Zapisywanie otrzymanego tokenu w stanie i SecureStore
            const token = response.data.access_token;
            await setToken(token);

            // useEffect w _layout.tsx automatycznie wykryje zmianę tokena i przeniesie do /(tabs)

        } catch (error: any) {
            console.error('Błąd logowania:', error.response?.data || error.message);
            Alert.alert('Błąd', 'Niepoprawne dane logowania lub błąd serwera');
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Smart Doniczka</Text>

            <TextInput
                style={styles.input}
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
            />

            <TextInput
                style={styles.input}
                placeholder="Hasło"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />

            <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
                {loading ? (
                    <ActivityIndicator color="#fff" />
                ) : (
                    <Text style={styles.buttonText}>Zaloguj się</Text>
                )}
            </TouchableOpacity>

            <Link href="/register" asChild>
                <TouchableOpacity style={{ marginTop: 20, alignItems: 'center' }}>
                    <Text style={{ color: '#2c3e50', fontSize: 16 }}>
                        Nie masz konta? <Text style={{ fontWeight: 'bold' }}>Zarejestruj się</Text>
                    </Text>
                </TouchableOpacity>
            </Link>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        padding: 20,
        backgroundColor: '#F5FCFF',
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 40,
        color: '#2c3e50',
    },
    input: {
        height: 50,
        backgroundColor: '#fff',
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        paddingHorizontal: 15,
        marginBottom: 15,
        fontSize: 16,
    },
    button: {
        height: 50,
        backgroundColor: '#27ae60',
        justifyContent: 'center',
        alignItems: 'center',
        borderRadius: 8,
        marginTop: 10,
    },
    buttonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '600',
    },
});