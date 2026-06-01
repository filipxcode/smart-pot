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
    type: string; // Zależnie od tego, jak backend definiuje typ eventu
    created_at: string;
}