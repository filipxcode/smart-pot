import React, { useState } from 'react';
import { View, Text, StyleSheet, Dimensions, ActivityIndicator, TouchableOpacity, ScrollView } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { LineChart } from 'react-native-chart-kit';
import { apiClient } from '@/api/client';
import { useDeviceStore } from '@/store/useDeviceStore';
import type { HistorySummary } from '@/types/api';

const screenWidth = Dimensions.get('window').width;

type SensorKey = 'air_temp' | 'air_hum' | 'root_temp' | 'soil_hum' | 'light_lux';

export default function StatisticsScreen() {
    const { selectedDeviceId } = useDeviceStore();
    const [days, setDays] = useState<number>(7);

    const { data: summary, isLoading, isError } = useQuery<HistorySummary>({
        queryKey: ['metricsSummary', selectedDeviceId, days],
        queryFn: async () => {
            const response = await apiClient.get(`/metrics/${selectedDeviceId}/summary?unit=day&amount=${days}`);
            return response.data;
        },
        enabled: !!selectedDeviceId,
    });

    const renderChart = (
        title: string,
        dataKey: SensorKey,
        rgbColor: string,
        suffix: string
    ) => {
        if (!summary || summary.buckets.length === 0) return null;

        const validBuckets = summary.buckets.filter(b => b[dataKey] !== null);
        if (validBuckets.length === 0) return null;

        const values = validBuckets.map(b => b[dataKey] as number);
        const isHourly = summary.granularity === 'hour';

        const labels = validBuckets.map((b, index) => {
            if (
                index === 0 ||
                index === Math.floor(validBuckets.length * 0.25) ||
                index === Math.floor(validBuckets.length * 0.5) ||
                index === Math.floor(validBuckets.length * 0.75) ||
                index === validBuckets.length - 1
            ) {
                const date = new Date(b.bucket);
                return isHourly
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
                        decimalPlaces: 1,
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
            ) : !summary || summary.buckets.length === 0 ? (
                <Text style={styles.emptyText}>Brak danych dla wybranego okresu.</Text>
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
    emptyText: { textAlign: 'center', color: '#7f8c8d', fontStyle: 'italic', marginTop: 40 },
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
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.05,
        shadowRadius: 4,
        elevation: 3,
    },
    chart: { borderRadius: 16 }
});
