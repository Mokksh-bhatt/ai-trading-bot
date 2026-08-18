import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001/api';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface Trade {
    id: number;
    model_name: string;
    strategy_tag: string;
    asset_class: string;
    symbol: string;
    status: string;
    quantity: number;
    entry_price: number;
    entry_time: string;
    exit_price: number | null;
    exit_time: string | null;
    unrealized_pnl: number | null;
    realized_pnl: number | null;
    simulated_fees: number | null;
    pnl_pct: number | null;
    reasoning_text: string;
    confidence: number;
}

export interface ModelStats {
    total_trades: number;
    closed_trades: number;
    win_rate_pct: number;
    cumulative_pnl_pct: number;
    cumulative_realized_pnl: number;
    live_unrealized_pnl: number;
    total_pnl: number;
}

export interface HistoricalPrice {
    time: string;
    price: number;
}

export const fetchModels = async (): Promise<string[]> => {
    const res = await apiClient.get('/models');
    return res.data.models;
};

export const fetchTrades = async (modelName: string): Promise<Trade[]> => {
    const res = await apiClient.get(`/trades/${modelName}`);
    return res.data.trades;
};

export const fetchStats = async (modelName: string): Promise<ModelStats> => {
    const res = await apiClient.get(`/stats/${modelName}`);
    return res.data;
};

export const fetchHistory = async (symbol: string, assetClass: string): Promise<HistoricalPrice[]> => {
    const res = await apiClient.get(`/history?symbol=${encodeURIComponent(symbol)}&asset_class=${encodeURIComponent(assetClass)}`);
    return res.data.history;
};

export const fetchMacroBias = async (): Promise<Record<string, {bias: string, reasoning: string}>> => {
    const res = await apiClient.get('/macro_bias');
    return res.data.macro_bias;
};

export const triggerCycle = async (): Promise<void> => {
    await apiClient.post('/trigger');
};
