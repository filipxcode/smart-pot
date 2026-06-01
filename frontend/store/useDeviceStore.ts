import { create } from 'zustand';

interface DeviceState {
    selectedDeviceId: number | null;
    setSelectedDeviceId: (id: number | null) => void;
}

export const useDeviceStore = create<DeviceState>((set) => ({
    selectedDeviceId: null,
    setSelectedDeviceId: (id) => set({ selectedDeviceId: id }),
}));