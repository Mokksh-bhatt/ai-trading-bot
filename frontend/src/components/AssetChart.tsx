import React, { useEffect, useState } from 'react';
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Scatter } from 'recharts';
import { fetchHistory } from '../api/client';
import type { HistoricalPrice, Trade } from '../api/client';

interface AssetChartProps {
    symbol: string;
    assetClass: string;
    trades: Trade[];
}

const AssetChart: React.FC<AssetChartProps> = ({ symbol, assetClass, trades }) => {
    const [data, setData] = useState<HistoricalPrice[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadHistory = async () => {
            setLoading(true);
            try {
                const history = await fetchHistory(symbol, assetClass);
                setData(history);
            } catch (e) {
                console.error("Error fetching history:", e);
            } finally {
                setLoading(false);
            }
        };
        loadHistory();
        const interval = setInterval(loadHistory, 60000); // refresh every minute
        return () => clearInterval(interval);
    }, [symbol, assetClass]);

    if (loading && data.length === 0) {
        return <div className="h-64 flex items-center justify-center text-slate-500">Loading chart data...</div>;
    }

    const chartData = data.map(d => ({
        ...d,
        displayTime: new Date(d.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: new Date(d.time).getTime()
    }));

    const buys = trades.filter(t => t.symbol === symbol).map(t => ({
        time: new Date(t.entry_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: new Date(t.entry_time).getTime(),
        price: t.entry_price,
        type: 'buy'
    }));

    const sells = trades.filter(t => t.symbol === symbol && t.exit_price !== null).map(t => ({
        time: new Date(t.exit_time!).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: new Date(t.exit_time!).getTime(),
        price: t.exit_price,
        type: 'sell'
    }));

    const mergedData = chartData.map(d => {
        const minute = 60 * 1000;
        const buy = buys.find(b => Math.abs(b.timestamp - d.timestamp) < minute * 1.5);
        const sell = sells.find(s => Math.abs(s.timestamp - d.timestamp) < minute * 1.5);
        return {
            ...d,
            buyPrice: buy ? buy.price : null,
            sellPrice: sell ? sell.price : null,
        };
    });

    const renderCustomShape = (props: any) => {
        const { cx, cy, fill } = props;
        if (!cx || !cy) return null;
        if (fill === '#10b981') {
            return (
                <svg x={cx - 10} y={cy - 10} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400 drop-shadow-md">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="5 12 12 5 19 12"></polyline>
                </svg>
            );
        } else {
            return (
                <svg x={cx - 10} y={cy - 10} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-rose-400 drop-shadow-md">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <polyline points="19 12 12 19 5 12"></polyline>
                </svg>
            );
        }
    };

    const minPrice = Math.min(...chartData.map(d => d.price));
    const maxPrice = Math.max(...chartData.map(d => d.price));
    const domain = [minPrice * 0.998, maxPrice * 1.002];

    return (
        <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={mergedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="displayTime" stroke="#94a3b8" tick={{fontSize: 12}} minTickGap={30} />
                    <YAxis stroke="#94a3b8" tick={{fontSize: 12}} domain={domain} tickFormatter={(val) => `$${val.toFixed(2)}`} width={80} />
                    <Tooltip 
                        contentStyle={{backgroundColor: '#1e293b', border: '1px solid #334155'}}
                        itemStyle={{color: '#f8fafc'}}
                        labelStyle={{color: '#94a3b8'}}
                    />
                    <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Scatter name="Buy" dataKey="buyPrice" fill="#10b981" shape={renderCustomShape} isAnimationActive={false} />
                    <Scatter name="Sell" dataKey="sellPrice" fill="#f43f5e" shape={renderCustomShape} isAnimationActive={false} />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
};

export default AssetChart;
