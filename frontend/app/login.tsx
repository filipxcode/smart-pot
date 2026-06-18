import React, { useState } from 'react';
import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
    StyleSheet,
    ActivityIndicator,
    KeyboardAvoidingView,
    TouchableWithoutFeedback,
    Keyboard,
    Platform
} from 'react-native';
import { useAuthStore } from '@/store/useAuthStore';
import { apiClient } from '@/api/client';
import { Link } from 'expo-router';

export default function LoginScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const [errorMsg, setErrorMsg] = useState('');
    const [focusedInput, setFocusedInput] = useState('');

    const setToken = useAuthStore((state) => state.setToken);

    const handleLogin = async () => {
        if (!email || !password) {
            setErrorMsg('Wpisz email i hasło');
            return;
        }

        setErrorMsg('');
        setLoading(true);
        try {
            const params = new URLSearchParams();
            params.append('username', email);
            params.append('password', password);

            const response = await apiClient.post('/auth/jwt/login', params.toString(), {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });

            const token = response.data.access_token;
            await setToken(token);

        } catch (error: any) {
            console.error('Błąd logowania:', error.response?.data || error.message);
            setErrorMsg('Niepoprawne dane logowania lub błąd serwera');
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={{ flex: 1 }}
        >
            <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
                <View style={styles.container}>
                    <Text style={styles.title}>Smart Doniczka</Text>

                    <TextInput
                        style={[styles.input, focusedInput === 'email' && styles.inputFocused]}
                        placeholder="Email"
                        placeholderTextColor="#7f8c8d"
                        value={email}
                        onChangeText={setEmail}
                        onFocus={() => setFocusedInput('email')}
                        onBlur={() => setFocusedInput('')}
                        autoCapitalize="none"
                        keyboardType="email-address"
                        textContentType="emailAddress"
                        autoComplete="email"
                    />

                    <TextInput
                        style={[styles.input, focusedInput === 'password' && styles.inputFocused]}
                        placeholder="Hasło"
                        placeholderTextColor="#7f8c8d"
                        value={password}
                        onChangeText={setPassword}
                        onFocus={() => setFocusedInput('password')}
                        onBlur={() => setFocusedInput('')}
                        secureTextEntry
                        textContentType="password"
                        autoComplete="password"
                    />

                    {errorMsg ? <Text style={styles.errorText}>{errorMsg}</Text> : null}

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
            </TouchableWithoutFeedback>
        </KeyboardAvoidingView>
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
    inputFocused: {
        borderColor: '#27ae60',
        borderWidth: 2,
    },
    errorText: {
        color: '#e74c3c',
        marginBottom: 15,
        textAlign: 'center',
        fontWeight: '600',
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