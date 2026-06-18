import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as DocumentPicker from 'expo-document-picker';
import { apiClient } from '@/api/client';
import { useDeviceStore } from '@/store/useDeviceStore';
import { useAuthStore } from '@/store/useAuthStore';
import { Device } from '@/types/api';

export default function SettingsScreen() {
    const queryClient = useQueryClient();
    const { selectedDeviceId, setSelectedDeviceId } = useDeviceStore();
    const logout = useAuthStore((state) => state.logout);

    const [newName, setNewName] = useState('');
    const [newSerial, setNewSerial] = useState('');

    const [docTitle, setDocTitle] = useState('');
    const [selectedFile, setSelectedFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);

    const { data: devices, isLoading, isError } = useQuery<Device[]>({
        queryKey: ['devices'],
        queryFn: async () => {
            const response = await apiClient.get('/devices');
            return response.data;
        },
    });

    const addDeviceMutation = useMutation({
        mutationFn: async (newDevice: { name: string; serial: string }) => {
            const response = await apiClient.post('/devices', newDevice);
            return response.data;
        },
        onSuccess: (newDevice) => {
            queryClient.invalidateQueries({ queryKey: ['devices'] });
            setNewName('');
            setNewSerial('');
            setSelectedDeviceId(newDevice.id);
            Alert.alert('Sukces', 'Sparowano nową doniczkę!');
        },
        onError: () => {
            Alert.alert('Błąd', 'Nie udało się dodać urządzenia. Sprawdź numer seryjny.');
        }
    });

    const uploadDocMutation = useMutation({
        mutationFn: async () => {
            if (!selectedFile || !docTitle) throw new Error("Brak tytułu lub pliku");

            const formData = new FormData();
            formData.append('title', docTitle);

            formData.append('file', {
                uri: selectedFile.uri,
                name: selectedFile.name,
                type: selectedFile.mimeType || 'application/pdf',
            } as any);

            const response = await apiClient.post('/file', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data;
        },
        onSuccess: () => {
            Alert.alert('Sukces', 'Dokument został pomyślnie wgrany i rozpoczęto jego przetwarzanie!');
            setDocTitle('');
            setSelectedFile(null);
        },
        onError: (error: any) => {
            console.error(error.response?.data || error);
            Alert.alert('Błąd', 'Nie udało się wgrać dokumentu. Upewnij się, że to poprawny plik PDF (maksymalnie 10MB).');
        }
    });

    const handleAddDevice = () => {
        if (!newName || !newSerial) {
            Alert.alert('Błąd', 'Uzupełnij nazwę i numer seryjny');
            return;
        }
        addDeviceMutation.mutate({ name: newName, serial: newSerial });
    };

    const handlePickDocument = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({
                type: 'application/pdf',
                copyToCacheDirectory: true,
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                const file = result.assets[0];
                setSelectedFile(file);
                if (!docTitle) setDocTitle(file.name.replace('.pdf', ''));
            }
        } catch (error) {
            console.error("Błąd podczas wyboru pliku:", error);
        }
    };

    const handleUploadDocument = () => {
        if (!docTitle) {
            Alert.alert('Błąd', 'Wpisz tytuł dokumentu');
            return;
        }
        if (!selectedFile) {
            Alert.alert('Błąd', 'Najpierw wybierz plik PDF z urządzenia');
            return;
        }
        uploadDocMutation.mutate();
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
        <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
            <Text style={styles.header}>Twoje doniczki</Text>

            {isLoading ? (
                <ActivityIndicator size="large" color="#2980b9" />
            ) : isError ? (
                <Text style={styles.errorText}>Błąd pobierania urządzeń.</Text>
            ) : (
                <View style={styles.listContainer}>
                    {devices?.length === 0 ? (
                        <Text style={styles.emptyText}>Brak dodanych doniczek.</Text>
                    ) : (
                        devices?.map((item) => (
                            <View key={item.id.toString()}>
                                {renderDeviceItem({ item })}
                            </View>
                        ))
                    )}
                </View>
            )}

            <View style={styles.cardSection}>
                <Text style={styles.subHeader}>Dodaj nową doniczkę</Text>
                <TextInput
                    style={styles.input}
                    placeholder="Nazwa (np. Paprotka w salonie)"
                    placeholderTextColor="#7f8c8d"
                    value={newName}
                    onChangeText={setNewName}
                />
                <TextInput
                    style={styles.input}
                    placeholder="Numer seryjny (SN)"
                    placeholderTextColor="#7f8c8d"
                    value={newSerial}
                    onChangeText={setNewSerial}
                />
                <TouchableOpacity
                    style={styles.primaryButton}
                    onPress={handleAddDevice}
                    disabled={addDeviceMutation.isPending}
                >
                    {addDeviceMutation.isPending ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.primaryButtonText}>Sparuj urządzenie</Text>
                    )}
                </TouchableOpacity>
            </View>

            <View style={styles.cardSection}>
                <Text style={styles.subHeader}>Wgraj bazę danych (PDF)</Text>
                <TextInput
                    style={styles.input}
                    placeholder="Tytuł dokumentu"
                    placeholderTextColor="#7f8c8d"
                    value={docTitle}
                    onChangeText={setDocTitle}
                />

                <TouchableOpacity style={styles.secondaryButton} onPress={handlePickDocument}>
                    <Text style={styles.secondaryButtonText}>
                        {selectedFile ? `Wybrano: ${selectedFile.name}` : 'Wybierz plik z telefonu'}
                    </Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={[styles.primaryButton, { marginTop: 10, backgroundColor: '#8e44ad' }]}
                    onPress={handleUploadDocument}
                    disabled={uploadDocMutation.isPending || !selectedFile}
                >
                    {uploadDocMutation.isPending ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.primaryButtonText}>Wyślij do bazy</Text>
                    )}
                </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.logoutButton} onPress={logout}>
                <Text style={styles.logoutText}>Wyloguj się</Text>
            </TouchableOpacity>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#F5FCFF', padding: 20 },
    header: { fontSize: 24, fontWeight: 'bold', marginBottom: 15, color: '#2c3e50', marginTop: 10 },
    subHeader: { fontSize: 18, fontWeight: 'bold', marginBottom: 10, color: '#2c3e50' },
    listContainer: { marginBottom: 20 },
    deviceCard: { backgroundColor: '#fff', padding: 15, borderRadius: 8, marginBottom: 10, borderWidth: 1, borderColor: '#ddd' },
    deviceCardSelected: { borderColor: '#27ae60', backgroundColor: '#eafaf1' },
    deviceName: { fontSize: 18, fontWeight: 'bold', color: '#333' },
    deviceSerial: { fontSize: 14, color: '#7f8c8d', marginTop: 4 },
    textSelected: { color: '#27ae60' },
    activeLabel: { position: 'absolute', right: 15, top: 15, color: '#27ae60', fontWeight: 'bold' },
    cardSection: { backgroundColor: '#fff', padding: 15, borderRadius: 8, borderWidth: 1, borderColor: '#ddd', marginBottom: 20 },
    input: { height: 45, borderWidth: 1, borderColor: '#eee', borderRadius: 6, paddingHorizontal: 10, marginBottom: 10, color: '#2c3e50', backgroundColor: '#fafafa' },
    primaryButton: { backgroundColor: '#2980b9', padding: 12, borderRadius: 6, alignItems: 'center' },
    primaryButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
    secondaryButton: { backgroundColor: '#ecf0f1', padding: 12, borderRadius: 6, alignItems: 'center', borderWidth: 1, borderColor: '#bdc3c7' },
    secondaryButtonText: { color: '#2c3e50', fontWeight: '600', fontSize: 14 },
    logoutButton: { padding: 15, alignItems: 'center', marginTop: 10 },
    logoutText: { color: '#e74c3c', fontSize: 16, fontWeight: 'bold' },
    emptyText: { textAlign: 'center', color: '#7f8c8d', fontStyle: 'italic', marginVertical: 20 },
    errorText: { color: '#e74c3c', textAlign: 'center', marginBottom: 10 }
});