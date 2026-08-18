import React, { useEffect, useState } from 'react';
import { fetchModels, fetchStats } from '../api/client';
import type { ModelStats } from '../api/client';
import { Link } from 'react-router-dom';

const DashboardSummary: React.FC = () => {
    const [stats, setStats] = useState<Record<string, ModelStats>>({});
    const [models, setModels] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    const loadData = async () => {
        try {
            const fetchedModels = await fetchModels();
            setModels(fetchedModels);
            const statsMap: Record<string, ModelStats> = {};
            for (const m of fetchedModels) {
                statsMap[m] = await fetchStats(m);
            }
            setStats(statsMap);
        } catch (error) {
            console.error("Error loading dashboard summary:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 1500); // 1.5s ultra-fast UI updates
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return <div className="p-8 text-center text-gray-400">Loading Observatory...</div>;
    }

    return (
        <div className="bg-slate-900 rounded-xl p-6 shadow-xl shadow-black/50 border border-slate-800">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-slate-100">Models Summary</h2>
                    <p className="text-sm text-slate-400">Live observation across all asset classes & timeframes</p>
                </div>
                <div className="flex items-center space-x-2">
                    <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                    </span>
                    <span className="text-xs text-emerald-400 font-medium">Auto-refreshing</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {models.map(model => (
                    <Link to={`/model/${model}`} key={model} className="block transition-transform hover:-translate-y-1">
                        <div className="bg-slate-800 rounded-lg p-5 border border-slate-700 hover:border-blue-500/50 cursor-pointer h-full transition-all">
                            <h3 className="text-xl font-semibold text-blue-400 mb-4 flex items-center justify-between">
                                <span>{model}</span>
                                <span className="text-xs font-normal px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                                    {model === 'OllamaTrader' ? 'Local LLM (Qwen 2.5)' : 'Rule Baseline'}
                                </span>
                            </h3>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Win Rate</p>
                                    <p className="text-2xl font-light text-slate-200">
                                        {(stats[model]?.win_rate_pct ?? 0).toFixed(1)}%
                                    </p>
                                </div>
                                <div>
                                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Total PnL</p>
                                    <p className={`text-2xl font-light ${(stats[model]?.cumulative_pnl_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                        {(stats[model]?.cumulative_pnl_pct ?? 0).toFixed(2)}%
                                    </p>
                                </div>
                                <div className="col-span-2">
                                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Trades Recorded</p>
                                    <p className="text-lg text-slate-300">
                                        <span className="font-semibold text-white">{stats[model]?.closed_trades ?? 0}</span> closed / <span className="font-semibold text-white">{stats[model]?.total_trades ?? 0}</span> total
                                    </p>
                                </div>
                            </div>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
};

export default DashboardSummary;
