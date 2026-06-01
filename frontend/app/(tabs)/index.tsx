import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { apiClient } from '@/api/client';
import { useDeviceStore } from '@/store/useDeviceStore';
import { Metric } from '@/types/api';
import {randomInt} from "node:crypto";

export default function HomeScreen() {
    const { selectedDeviceId } = useDeviceStore();
    const router = useRouter();

    // Pobieranie najnowszych metryk
    const { data: latestMetric, isLoading, isError } = useQuery<Metric | null>({
        queryKey: ['latestMetric', selectedDeviceId],
        queryFn: async () => {
            const response = await apiClient.get(`/metrics/${selectedDeviceId}/latest`);
            return response.data;
        },
        enabled: !!selectedDeviceId,
        // Odpytuj backend co 5000 ms (5 sekund)
        refetchInterval: 5000,
    });

    // Akcja podlewania
    const waterPlantMutation = useMutation({
        mutationFn: async () => {
            await apiClient.post(`/devices/${selectedDeviceId}/water`);
        },
        onSuccess: () => {
            Alert.alert('Sukces', 'Sygnał podlewania został wysłany do doniczki!');
        },
        onError: () => {
            Alert.alert('Błąd', 'Nie udało się podlać rośliny. Sprawdź połączenie.');
        }
    });

    const handleWaterPlant = () => {
        waterPlantMutation.mutate();
    };

    // Obsługa przypadku, gdy użytkownik nie ma jeszcze wybranej doniczki
    if (!selectedDeviceId) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.warningText}>Brak wybranej doniczki.</Text>
                <Text style={styles.subWarningText}>Przejdź do ustawień, aby dodać lub wybrać urządzenie.</Text>
                <TouchableOpacity style={styles.button} onPress={() => router.push('/settings' as any)}>
                    <Text style={styles.buttonText}>Przejdź do ustawień</Text>
                </TouchableOpacity>
            </View>
        );
    }

    // ===================================================================
    // CZĘŚĆ POMOCNICZA PRZY DEBUGGOWANIU, DO USUNIĘCIA W FINALNEJ WERSJI
    // ===================================================================

    // Funkcja pomocnicza dla liczb zmiennoprzecinkowych (np. temperatura 23.5)
    const getRandomFloat = (min: number, max: number) => {
        return parseFloat((Math.random() * (max - min) + min).toFixed(1));
    };

    // Funkcja pomocnicza dla liczb całkowitych (np. wilgotność gleby 45)
    const getRandomInt = (min: number, max: number) => {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    };

    const handleSendMockData = async () => {
        try {
            await apiClient.post('/metrics', {
                device_id: selectedDeviceId,
                air_temp: getRandomFloat(15.0, 30.0),
                air_hum: getRandomFloat(10.0, 70.0),
                root_temp: getRandomFloat(10.0, 25.0),
                soil_hum: getRandomInt(30, 80), // Oczekiwany int według backendu
                light_lux: getRandomFloat(1000.0, 40000.0)
            });
        } catch (error) {
            console.error('Błąd wysyłania testowych danych:', error);
            Alert.alert('Błąd', 'Nie udało się wysłać danych testowych.');
        }
    };
    // ===================================================================
    //                              KONIEC
    // ===================================================================

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.header}>Stan Twojej Rośliny</Text>
            <Text style={styles.subHeader}>ID Urządzenia: {selectedDeviceId}</Text>

            {isLoading ? (
                <View style={styles.centerContainer}>
                    <ActivityIndicator size="large" color="#27ae60" />
                    <Text style={{ marginTop: 10 }}>Pobieranie danych z czujników...</Text>
                </View>
            ) : isError ? (
                <Text style={styles.warningText}>Błąd pobierania danych. Spróbuj ponownie później.</Text>
            ) : !latestMetric ? (
                <Text style={styles.warningText}>Brak danych z czujników. Upewnij się, że urządzenie jest podłączone i wysyła dane.</Text>
            ) : (
                <View style={styles.metricsContainer}>

                    <View style={styles.metricCard}>
                        <Text style={styles.metricLabel}>Wilgotność gleby</Text>
                        <Text style={styles.metricValue}>
                            {latestMetric.soil_hum !== null ? `${latestMetric.soil_hum}%` : 'Brak danych'}
                        </Text>
                    </View>

                    <View style={styles.row}>
                        <View style={[styles.metricCard, styles.halfCard]}>
                            <Text style={styles.metricLabel}>Temp. Powietrza</Text>
                            <Text style={styles.metricValue}>
                                {latestMetric.air_temp !== null ? `${latestMetric.air_temp.toFixed(1)}°C` : '--'}
                            </Text>
                        </View>
                        <View style={[styles.metricCard, styles.halfCard]}>
                            <Text style={styles.metricLabel}>Wilg. Powietrza</Text>
                            <Text style={styles.metricValue}>
                                {latestMetric.air_hum !== null ? `${latestMetric.air_hum.toFixed(1)}%` : '--'}
                            </Text>
                        </View>
                    </View>

                    <View style={styles.row}>
                        <View style={[styles.metricCard, styles.halfCard]}>
                            <Text style={styles.metricLabel}>Temp. Korzeni</Text>
                            <Text style={styles.metricValue}>
                                {latestMetric.root_temp !== null ? `${latestMetric.root_temp.toFixed(1)}°C` : '--'}
                            </Text>
                        </View>
                        <View style={[styles.metricCard, styles.halfCard]}>
                            <Text style={styles.metricLabel}>Nasłonecznienie</Text>
                            <Text style={styles.metricValue}>
                                {latestMetric.light_lux !== null ? `${latestMetric.light_lux.toFixed(0)} lx` : '--'}
                            </Text>
                        </View>
                    </View>

                    <Text style={styles.timestamp}>
                        Ostatnia aktualizacja: {new Date(latestMetric.created_at).toLocaleTimeString()}
                    </Text>
                </View>
            )}

            {/* Przycisk podlewania */}
            <TouchableOpacity
                style={[styles.waterButton, waterPlantMutation.isPending && styles.waterButtonDisabled]}
                onPress={handleWaterPlant}
                disabled={waterPlantMutation.isPending || isLoading}
            >
                {waterPlantMutation.isPending ? (
                    <ActivityIndicator color="#fff" />
                ) : (
                    <Text style={styles.waterButtonText}>💧 Podlej Teraz</Text>
                )}
            </TouchableOpacity>

            {/*Przycisk testowych danych*/}
            <TouchableOpacity
                style={[styles.button, { backgroundColor: '#e67e22', marginBottom: 20, marginTop: 10 }]}
                onPress={handleSendMockData}
            >
                <Text style={styles.buttonText}>🛠 Wyślij testowe dane</Text>
            </TouchableOpacity>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flexGrow: 1, padding: 20, backgroundColor: '#F5FCFF' },
    centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
    header: { fontSize: 26, fontWeight: 'bold', color: '#2c3e50', textAlign: 'center' },
    subHeader: { fontSize: 14, color: '#7f8c8d', textAlign: 'center', marginBottom: 20 },
    warningText: { fontSize: 20, fontWeight: 'bold', color: '#e74c3c', marginBottom: 10 },
    subWarningText: { fontSize: 16, color: '#7f8c8d', textAlign: 'center', marginBottom: 20 },
    metricsContainer: { marginBottom: 30 },
    metricCard: { backgroundColor: '#fff', padding: 20, borderRadius: 12, marginBottom: 15, borderWidth: 1, borderColor: '#eee', alignItems: 'center', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 4, elevation: 2 },
    row: { flexDirection: 'row', justifyContent: 'space-between' },
    halfCard: { width: '48%' },
    metricLabel: { fontSize: 14, color: '#7f8c8d', marginBottom: 5, textAlign: 'center' },
    metricValue: { fontSize: 22, fontWeight: 'bold', color: '#2c3e50' },
    timestamp: { textAlign: 'center', color: '#95a5a6', fontSize: 12, marginTop: 5 },
    button: { backgroundColor: '#3498db', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 8 },
    buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
    waterButton: { backgroundColor: '#3498db', padding: 18, borderRadius: 12, alignItems: 'center', marginTop: 'auto', shadowColor: '#3498db', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 5, elevation: 4 },
    waterButtonDisabled: { backgroundColor: '#95a5a6' },
    waterButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 18 }
});