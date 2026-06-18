export interface User {
    id: string; // backend używa UUID
    email: string;
    is_active: boolean;
}

export interface Device {
    id: number;
    name: string;
    serial: string;
    owner_id: string; // UUID
}

export interface Metric {
    id: number;
    device_id: number;
    air_temp: number | null;
    air_hum: number | null;
    root_temp: number | null;
    soil_hum: number | null; // backend zwraca tu int | null
    light_lux: number | null;
    created_at: string; // ISO 8601 format
}

export interface DeviceEvent {
    id: string;
    device_id: number;
    event_type: string;
    created_at: string;
}

export interface MetricBucket {
    bucket: string; // ISO 8601 - start of bucket
    count: number;
    air_temp: number | null;
    air_hum: number | null;
    root_temp: number | null;
    soil_hum: number | null;
    light_lux: number | null;
}

export interface HistorySummary {
    unit: string;
    amount: number;
    granularity: string; // "hour" | "day" | "week" | "month"
    start: string; // ISO 8601
    buckets: MetricBucket[];
}