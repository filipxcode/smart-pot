import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { apiClient } from '../api/client';

export default function RegisterScreen() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState(''); // Nowy stan dla powtórzonego hasła
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleRegister = async () => {
        // Sprawdzanie, czy wszystkie pola są wypełnione
        if (!email || !password || !confirmPassword) {
            Alert.alert('Błąd', 'Proszę wypełnić wszystkie pola');
            return;
        }

        // Walidacja identyczności haseł
        if (password !== confirmPassword) {
            Alert.alert('Błąd', 'Podane hasła nie są identyczne');
            return;
        }

        setLoading(true);
        try {
            await apiClient.post('/auth/register', {
                email: email,
                password: password,
            });

            Alert.alert('Sukces', 'Konto zostało pomyślnie utworzone! Możesz się teraz zalogować.');
            router.back();

        } catch (error: any) {
            console.error('Błąd rejestracji:', error.response?.data || error.message);
            Alert.alert('Błąd rejestracji', 'Nie udało się utworzyć konta. Być może użytkownik z tym adresem email już istnieje.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Stwórz konto</Text>

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

            <TextInput
                style={styles.input}
                placeholder="Powtórz hasło"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
            />

            <TouchableOpacity style={styles.button} onPress={handleRegister} disabled={loading}>
                {loading ? (
                    <ActivityIndicator color="#fff" />
                ) : (
                    <Text style={styles.buttonText}>Zarejestruj się</Text>
                )}
            </TouchableOpacity>

            <TouchableOpacity style={styles.backButton} onPress={() => router.back()} disabled={loading}>
                <Text style={styles.backButtonText}>Wróć do logowania</Text>
            </TouchableOpacity>
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
        backgroundColor: '#2980b9',
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
    backButton: {
        marginTop: 20,
        alignItems: 'center',
    },
    backButtonText: {
        color: '#7f8c8d',
        fontSize: 16,
    }
});