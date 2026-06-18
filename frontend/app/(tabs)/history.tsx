import React, { useState } from 'react';
import { View, Text, StyleSheet, Dimensions, ActivityIndicator, TouchableOpacity, ScrollView } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { LineChart } from 'react-native-chart-kit';
import { apiClient } from '@/api/client';
import { useDeviceStore } from '@/store/useDeviceStore';
import { Metric } from '@/types/api';

const screenWidth = Dimensions.get('window').width;

export default function StatisticsScreen() {
    const { selectedDeviceId } = useDeviceStore();
    const [days, setDays] = useState<number>(7);

    const { data: historyData, isLoading, isError } = useQuery<Metric[]>({
        queryKey: ['metricsHistory', selectedDeviceId, days],
        queryFn: async () => {
            const response = await apiClient.get(`/metrics/${selectedDeviceId}/history?days=${days}`);
            return response.data.reverse();
        },
        enabled: !!selectedDeviceId,
    });

    // Funkcja generująca wykres
    const renderChart = (
        title: string,
        dataKey: keyof Metric,
        rgbColor: string,
        suffix: string
    ) => {
        if (!historyData || historyData.length === 0) return null;

        const validData = historyData.filter(m => m[dataKey] !== null);
        if (validData.length === 0) return null;

        const MAX_POINTS = 10;
        let sampledData = validData;

        if (validData.length > MAX_POINTS) {
            const step = (validData.length - 1) / (MAX_POINTS - 1);
            sampledData = [];
            for (let i = 0; i < MAX_POINTS; i++) {
                sampledData.push(validData[Math.round(i * step)]);
            }
        }

        const values = sampledData.map(m => m[dataKey] as number);

        const labels = sampledData.map((m, index) => {
            if (
                index === 0 ||                                     // Punkt 0%
                index === Math.floor(sampledData.length * 0.25) || // Punkt 25%
                index === Math.floor(sampledData.length * 0.5)  || // Punkt 50%
                index === Math.floor(sampledData.length * 0.75) || // Punkt 75%
                index === sampledData.length - 1                   // Punkt 100%
            ) {
                const date = new Date(m.created_at);
                return days === 1
                    ? `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
                    : `${date.getDate()}.${date.getMonth() + 1}`;
            }
            return '';
        });

        const chartDataObj = {
            labels,
            datasets: [
                {
                    data: values,
                    color: (opacity = 1) => `rgba(${rgbColor}, ${opacity})`,
                    strokeWidth: 3,
                }
            ],
            legend: [title]
        };

        return (
            <View key={dataKey} style={styles.chartCard}>
                <LineChart
                    data={chartDataObj}
                    width={screenWidth - 40}
                    height={220}
                    yAxisSuffix={suffix}
                    fromZero={suffix === "%"}
                    chartConfig={{
                        backgroundColor: '#ffffff',
                        backgroundGradientFrom: '#ffffff',
                        backgroundGradientTo: '#ffffff',
                        decimalPlaces: 1, // Wymuszenie 1 miejsca po przecinku
                        color: (opacity = 1) => `rgba(200, 200, 200, ${opacity})`,
                        labelColor: (opacity = 1) => `rgba(100, 100, 100, ${opacity})`,
                        style: { borderRadius: 16 },
                        propsForDots: {
                            r: "4",
                            strokeWidth: "2",
                            stroke: `rgb(${rgbColor})`
                        }
                    }}
                    formatYLabel={(value) => parseFloat(value).toFixed(1)}
                    bezier
                    style={styles.chart}
                />
            </View>
        );
    };

    if (!selectedDeviceId) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.warningText}>Brak wybranej doniczki.</Text>
            </View>
        );
    }

    return (
        <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
            <Text style={styles.header}>Historia pomiarów</Text>

            {/* Przyciski zakresu czasu */}
            <View style={styles.timeToggles}>
                {[1, 7, 30].map((range) => (
                    <TouchableOpacity
                        key={range}
                        style={[styles.toggleBtn, days === range && styles.toggleBtnActive]}
                        onPress={() => setDays(range)}
                    >
                        <Text style={[styles.toggleText, days === range && styles.toggleTextActive]}>
                            {range} {range === 1 ? 'dzień' : 'dni'}
                        </Text>
                    </TouchableOpacity>
                ))}
            </View>

            {isLoading ? (
                <View style={styles.centerContainer}>
                    <ActivityIndicator size="large" color="#27ae60" />
                </View>
            ) : isError ? (
                <Text style={styles.errorText}>Błąd pobierania historii pomiarów.</Text>
            ) : (
                <>
                    {renderChart("Wilgotność gleby", "soil_hum", "46, 204, 113", "%")}
                    {renderChart("Wilgotność powietrza", "air_hum", "52, 152, 219", "%")}
                    {renderChart("Temp. powietrza", "air_temp", "231, 76, 60", "°C")}
                </>
            )}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#F5FCFF' },
    scrollContent: { padding: 15, paddingBottom: 40 },
    centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', minHeight: 300 },
    header: { fontSize: 24, fontWeight: 'bold', color: '#2c3e50', marginBottom: 20, textAlign: 'center' },
    warningText: { fontSize: 18, color: '#e74c3c' },
    timeToggles: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
    toggleBtn: { flex: 1, marginHorizontal: 5, paddingVertical: 10, borderRadius: 8, backgroundColor: '#e0e6ed', alignItems: 'center' },
    toggleBtnActive: { backgroundColor: '#2980b9' },
    toggleText: { color: '#7f8c8d', fontWeight: 'bold' },
    toggleTextActive: { color: '#fff' },
    errorText: { color: '#e74c3c', textAlign: 'center', marginTop: 20 },

    chartCard: {
        backgroundColor: '#fff',
        borderRadius: 16,
        paddingVertical: 15,
        paddingHorizontal: 5,
        marginBottom: 20,
        borderWidth: 1,
        borderColor: '#ecf0f1',
        alignItems: 'center',
        // Cienie
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 3,
    },
    chart: {
        borderRadius: 16
    }
});