import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client'; // upewnij się, że ścieżka jest poprawna
import { useDeviceStore } from '@/store/useDeviceStore';
import { useAuthStore } from '@/store/useAuthStore';
import { Device } from '@/types/api';

export default function SettingsScreen() {
    const queryClient = useQueryClient();
    const { selectedDeviceId, setSelectedDeviceId } = useDeviceStore();
    const logout = useAuthStore((state) => state.logout);

    // Stany dla formularza nowej doniczki
    const [newName, setNewName] = useState('');
    const [newSerial, setNewSerial] = useState('');

    // Pobieranie listy urządzeń z backendu
    const { data: devices, isLoading, isError } = useQuery<Device[]>({
        queryKey: ['devices'],
        queryFn: async () => {
            const response = await apiClient.get('/devices');
            return response.data;
        },
    });

    // Mutacja do dodawania nowego urządzenia
    const addDeviceMutation = useMutation({
        mutationFn: async (newDevice: { name: string; serial: string }) => {
            const response = await apiClient.post('/devices', newDevice);
            return response.data;
        },
        onSuccess: (newDevice) => {
            // Odświeżamy listę urządzeń po sukcesie
            queryClient.invalidateQueries({ queryKey: ['devices'] });
            setNewName('');
            setNewSerial('');
            // Z miejsca ustawiamy nowe urządzenie jako wybrane
            setSelectedDeviceId(newDevice.id);
            Alert.alert('Sukces', 'Sparowano nową doniczkę!');
        },
        onError: () => {
            Alert.alert('Błąd', 'Nie udało się dodać urządzenia. Sprawdź numer seryjny.');
        }
    });

    const handleAddDevice = () => {
        if (!newName || !newSerial) {
            Alert.alert('Błąd', 'Uzupełnij nazwę i numer seryjny');
            return;
        }
        addDeviceMutation.mutate({ name: newName, serial: newSerial });
    };

    const renderDeviceItem = ({ item }: { item: Device }) => {
        const isSelected = item.id === selectedDeviceId;
        return (
            <TouchableOpacity
                style={[styles.deviceCard, isSelected && styles.deviceCardSelected]}
                onPress={() => setSelectedDeviceId(item.id)}
            >
                <Text style={[styles.deviceName, isSelected && styles.textSelected]}>{item.name}</Text>
                <Text style={[styles.deviceSerial, isSelected && styles.textSelected]}>SN: {item.serial}</Text>
                {isSelected && <Text style={styles.activeLabel}>Aktywna</Text>}
            </TouchableOpacity>
        );
    };

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Twoje doniczki</Text>

            {isLoading ? (
                <ActivityIndicator size="large" color="#2980b9" />
            ) : isError ? (
                <Text style={styles.errorText}>Błąd pobierania urządzeń.</Text>
            ) : (
                <FlatList
                    data={devices}
                    keyExtractor={(item) => item.id.toString()}
                    renderItem={renderDeviceItem}
                    ListEmptyComponent={<Text style={styles.emptyText}>Brak dodanych doniczek.</Text>}
                    style={styles.list}
                />
            )}

            <View style={styles.addSection}>
                <Text style={styles.subHeader}>Dodaj nową doniczkę</Text>
                <TextInput
                    style={styles.input}
                    placeholder="Nazwa (np. Paprotka w salonie)"
                    value={newName}
                    onChangeText={setNewName}
                />
                <TextInput
                    style={styles.input}
                    placeholder="Numer seryjny (SN)"
                    value={newSerial}
                    onChangeText={setNewSerial}
                />
                <TouchableOpacity
                    style={styles.addButton}
                    onPress={handleAddDevice}
                    disabled={addDeviceMutation.isPending}
                >
                    {addDeviceMutation.isPending ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.addButtonText}>Sparuj urządzenie</Text>
                    )}
                </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.logoutButton} onPress={logout}>
                <Text style={styles.logoutText}>Wyloguj się</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: '#F5FCFF' },
    header: { fontSize: 24, fontWeight: 'bold', marginBottom: 15, color: '#2c3e50' },
    subHeader: { fontSize: 18, fontWeight: 'bold', marginBottom: 10, color: '#2c3e50' },
    list: { flexGrow: 0, maxHeight: '40%', marginBottom: 20 },
    deviceCard: { backgroundColor: '#fff', padding: 15, borderRadius: 8, marginBottom: 10, borderWidth: 1, borderColor: '#ddd' },
    deviceCardSelected: { borderColor: '#27ae60', backgroundColor: '#eafaf1' },
    deviceName: { fontSize: 18, fontWeight: 'bold', color: '#333' },
    deviceSerial: { fontSize: 14, color: '#7f8c8d', marginTop: 4 },
    textSelected: { color: '#27ae60' },
    activeLabel: { position: 'absolute', right: 15, top: 15, color: '#27ae60', fontWeight: 'bold' },
    addSection: { backgroundColor: '#fff', padding: 15, borderRadius: 8, borderWidth: 1, borderColor: '#ddd', marginBottom: 20 },
    input: { height: 45, borderWidth: 1, borderColor: '#eee', borderRadius: 6, paddingHorizontal: 10, marginBottom: 10 },
    addButton: { backgroundColor: '#2980b9', padding: 12, borderRadius: 6, alignItems: 'center' },
    addButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
    logoutButton: { marginTop: 'auto', padding: 15, alignItems: 'center' },
    logoutText: { color: '#e74c3c', fontSize: 16, fontWeight: 'bold' },
    emptyText: { textAlign: 'center', color: '#7f8c8d', fontStyle: 'italic', marginVertical: 20 },
    errorText: { color: '#e74c3c', textAlign: 'center' }
});