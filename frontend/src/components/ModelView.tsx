import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchTrades, fetchStats, fetchMacroBias } from '../api/client';
import type { Trade, ModelStats } from '../api/client';
import { ArrowLeft, RefreshCw, Activity, CheckCircle2, TrendingUp, BarChart2 } from 'lucide-react';
import AssetChart from './AssetChart';

const TradeTable = ({ trades, isOpen, title, icon: Icon }: { trades: Trade[], isOpen: boolean, title: string, icon: any }) => (
    <div className="bg-slate-900 rounded-xl p-6 shadow-xl shadow-black/50 border border-slate-800 overflow-hidden mb-6">
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
                <Icon className={`w-5 h-5 ${isOpen ? 'text-amber-400' : 'text-emerald-400'}`} />
                <h3 className="text-lg font-semibold text-slate-200">{title}</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">{trades.length} entries</span>
        </div>
        <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                        <th className="py-3 px-4">Time</th>
                        <th className="py-3 px-4">Asset</th>
                        <th className="py-3 px-4">Direction</th>
                        <th className="py-3 px-4">Qty</th>
                        <th className="py-3 px-4">Entry</th>
                        {isOpen ? <th className="py-3 px-4">Current Price</th> : <th className="py-3 px-4">Exit</th>}
                        <th className="py-3 px-4">{isOpen ? 'Unrealized PnL' : 'Realized PnL'}</th>
                        <th className="py-3 px-4">Reasoning</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                    {trades.map(t => {
                        const pnlVal = isOpen ? t.unrealized_pnl : t.realized_pnl;
                        const pnlColor = (pnlVal || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400';
                        const currentPrice = isOpen && t.quantity > 0 
                            ? (t as any).direction === 'short' 
                                ? t.entry_price - (t.unrealized_pnl || 0) / t.quantity
                                : t.entry_price + (t.unrealized_pnl || 0) / t.quantity 
                            : t.entry_price;
                        
                        return (
                        <tr key={t.id} className="hover:bg-slate-800/50 transition-colors group">
                            <td className="py-3 px-4 text-slate-300 text-xs whitespace-nowrap">
                                {new Date(isOpen ? t.entry_time : (t.exit_time || t.entry_time)).toLocaleString()}
                            </td>
                            <td className="py-3 px-4">
                                <a 
                                    href={`https://www.tradingview.com/symbols/${t.symbol.replace('/', '')}/`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                                    title="View live chart on TradingView"
                                >
                                    {t.symbol}
                                    <span className="text-[10px] text-slate-500">↗</span>
                                </a>
                            </td>
                            <td className="py-3 px-4">
                                <span className={`px-2 py-0.5 text-xs font-semibold rounded ${(t as any).direction === 'short' ? 'bg-rose-900/50 text-rose-400 border border-rose-800' : 'bg-emerald-900/50 text-emerald-400 border border-emerald-800'}`}>
                                    {((t as any).direction || 'long').toUpperCase()}
                                </span>
                            </td>
                            <td className="py-3 px-4 text-slate-300 text-sm font-mono">{t.quantity?.toFixed(4) || '--'}</td>
                            <td className="py-3 px-4 text-slate-300 text-sm font-mono">${t.entry_price.toFixed(4)}</td>
                            <td className="py-3 px-4 text-slate-300 text-sm font-mono">
                                {isOpen ? (
                                    <span className="text-amber-400">${currentPrice.toFixed(4)}</span>
                                ) : (
                                    `$${t.exit_price?.toFixed(4)}`
                                )}
                            </td>
                            <td className="py-3 px-4">
                                <span className={`font-mono text-sm font-semibold ${pnlColor}`}>
                                    {(pnlVal || 0) > 0 ? '+' : ''}${pnlVal?.toFixed(2) || '0.00'}
                                    <span className="text-xs ml-1 text-slate-500">({(t.pnl_pct || 0) > 0 ? '+' : ''}{t.pnl_pct?.toFixed(2) || '0.00'}%)</span>
                                </span>
                            </td>
                            <td className="py-3 px-4 max-w-xs md:max-w-md">
                                <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-2 hover:line-clamp-none transition-all">
                                    {t.reasoning_text}
                                </p>
                            </td>
                        </tr>
                    )})}
                </tbody>
            </table>
            {trades.length === 0 && (
                <div className="text-center py-12 text-slate-500">
                    <p className="text-sm">No {isOpen ? 'open' : 'closed'} trades in this category.</p>
                </div>
            )}
        </div>
    </div>
);

const ModelView: React.FC = () => {
    const { modelName } = useParams<{ modelName: string }>();
    const [trades, setTrades] = useState<Trade[]>([]);
    const [stats, setStats] = useState<ModelStats | null>(null);
    const [biasInfo, setBiasInfo] = useState<Record<string, {bias: string, reasoning: string}>>({});
    const [loading, setLoading] = useState(true);

    const [chartAsset, setChartAsset] = useState<{symbol: string, assetClass: string}>({ symbol: 'BTC/USDT', assetClass: 'crypto' });

    const loadData = async () => {
        if (!modelName) return;
        try {
            const [tradesData, statsData, biasData] = await Promise.all([
                fetchTrades(modelName),
                fetchStats(modelName),
                fetchMacroBias()
            ]);
            setTrades(tradesData);
            setStats(statsData);
            setBiasInfo(biasData);
        } catch (error) {
            console.error("Error loading model data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 1500);
        return () => clearInterval(interval);
    }, [modelName]);

    if (loading) return <div className="p-8 text-center text-gray-400">Loading {modelName} data...</div>;

    const cryptoOpen = trades.filter(t => t.asset_class === 'crypto' && t.status === 'open');
    const cryptoClosed = trades.filter(t => t.asset_class === 'crypto' && t.status === 'closed');
    const stocksOpen = trades.filter(t => t.asset_class === 'stock' && t.status === 'open');
    const stocksClosed = trades.filter(t => t.asset_class === 'stock' && t.status === 'closed');

    const tradedSymbols = Array.from(new Set(trades.map(t => JSON.stringify({symbol: t.symbol, assetClass: t.asset_class}))));
    if (tradedSymbols.length === 0) {
        tradedSymbols.push(JSON.stringify({symbol: 'BTC/USDT', assetClass: 'crypto'}));
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                    <Link to="/" className="p-2 bg-slate-800 rounded-full hover:bg-slate-700 transition-colors">
                        <ArrowLeft className="w-5 h-5 text-slate-300" />
                    </Link>
                    <div>
                        <h2 className="text-3xl font-bold text-slate-100">{modelName}</h2>
                        <p className="text-xs text-slate-400">Live paper execution & statistical breakdown</p>
                    </div>
                </div>
                <button 
                    onClick={loadData}
                    className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-colors"
                >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Refresh</span>
                </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-1 bg-slate-900 rounded-xl p-6 shadow-xl shadow-black/50 border border-slate-800 flex flex-col justify-between">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                        Live Performance
                    </h3>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                            <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Total PnL (Live)</p>
                            <p className={`text-4xl font-light ${(stats?.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                ${(stats?.total_pnl ?? 0).toFixed(2)}
                            </p>
                            <div className="flex justify-between text-xs mt-2">
                                <span className="text-slate-400">Realized: ${(stats?.cumulative_realized_pnl ?? 0).toFixed(2)}</span>
                                <span className="text-slate-400">Unrealized: ${(stats?.live_unrealized_pnl ?? 0).toFixed(2)}</span>
                            </div>
                        </div>
                        <div>
                            <p className="text-slate-400 text-sm">Win Rate (Closed)</p>
                            <p className="text-2xl font-light text-slate-100">{(stats?.win_rate_pct ?? 0).toFixed(1)}%</p>
                        </div>
                        <div className="flex justify-between">
                            <div>
                                <p className="text-slate-400 text-xs">Total Trades</p>
                                <p className="text-lg text-slate-100">{stats?.total_trades ?? 0}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-slate-400 text-xs">Active Open</p>
                                <p className="text-lg text-slate-100 text-amber-400 font-semibold">{trades.filter(t=>t.status==='open').length}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="lg:col-span-3 bg-slate-900 rounded-xl p-6 shadow-xl shadow-black/50 border border-slate-800">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                            <BarChart2 className="w-5 h-5 text-purple-400" />
                            Live Trade Visualization
                        </h3>
                        <div className="flex gap-2">
                            {tradedSymbols.slice(0, 5).map(sStr => {
                                const s = JSON.parse(sStr);
                                const isSelected = s.symbol === chartAsset.symbol;
                                return (
                                    <button 
                                        key={s.symbol}
                                        onClick={() => setChartAsset(s)}
                                        className={`px-3 py-1 text-xs rounded-md font-semibold transition-colors ${
                                            isSelected ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                                        }`}
                                    >
                                        {s.symbol}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                    <div className="w-full">
                        <AssetChart symbol={chartAsset.symbol} assetClass={chartAsset.assetClass} trades={trades} />
                    </div>
                    <div className="flex items-center justify-center gap-6 mt-4 text-xs font-medium text-slate-400">
                        <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-emerald-500 rounded-sm"></span> AI BUY Point</span>
                        <span className="flex items-center gap-1.5"><span className="w-3 h-3 bg-rose-500 rounded-sm"></span> AI SELL Point</span>
                    </div>
                </div>
            </div>

            <div className="mt-8 bg-slate-900 rounded-xl p-6 shadow-xl border border-slate-800">
                <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-400" />
                    Live AI Macro Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(biasInfo).map(([symbol, data]) => (
                        <div key={symbol} className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-bold text-blue-400">{symbol}</span>
                                <span className={`px-2 py-1 text-xs font-semibold rounded uppercase tracking-wider ${data.bias === 'bullish' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800' : data.bias === 'bearish' ? 'bg-rose-900/50 text-rose-400 border border-rose-800' : 'bg-slate-700 text-slate-300 border border-slate-600'}`}>
                                    {data.bias}
                                </span>
                            </div>
                            <p className="text-xs text-slate-300 leading-relaxed max-h-32 overflow-y-auto font-sans pr-2 custom-scrollbar">
                                {data.reasoning}
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="mt-12">
                <h2 className="text-2xl font-bold text-slate-100 mb-6">Crypto Markets</h2>
                <TradeTable trades={cryptoOpen.slice(0, 6)} isOpen={true} title="Live Open Positions (Crypto)" icon={Activity} />
                <TradeTable trades={cryptoClosed.slice(0, 6)} isOpen={false} title="Trade History (Crypto) - Latest 6" icon={CheckCircle2} />
            </div>

            <div className="mt-12">
                <h2 className="text-2xl font-bold text-slate-100 mb-6">Stock Markets</h2>
                <TradeTable trades={stocksOpen.slice(0, 6)} isOpen={true} title="Live Open Positions (Stocks)" icon={Activity} />
                <TradeTable trades={stocksClosed.slice(0, 6)} isOpen={false} title="Trade History (Stocks) - Latest 6" icon={CheckCircle2} />
            </div>
        </div>
    );
};

export default ModelView;
