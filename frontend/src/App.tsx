import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import DashboardSummary from './components/DashboardSummary';
import ModelView from './components/ModelView';
import { Activity, Play, CheckCircle2 } from 'lucide-react';
import { triggerCycle } from './api/client';

const App: React.FC = () => {
    const [triggering, setTriggering] = useState(false);
    const [triggeredMsg, setTriggeredMsg] = useState(false);

    const handleTrigger = async () => {
        setTriggering(true);
        try {
            await triggerCycle();
            setTriggeredMsg(true);
            setTimeout(() => setTriggeredMsg(false), 3000);
        } catch (e) {
            console.error("Failed to trigger cycle:", e);
        } finally {
            setTriggering(false);
        }
    };

    return (
        <Router>
            <div className="min-h-screen bg-slate-950 text-slate-300 font-sans">
                <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-10">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex items-center justify-between h-16">
                            <div className="flex items-center space-x-3">
                                <Activity className="w-6 h-6 text-blue-500 animate-pulse" />
                                <Link to="/" className="text-xl font-bold text-slate-100 hover:text-white transition-colors">
                                    AI Trading Observatory
                                </Link>
                                <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full animate-pulse flex items-center gap-1.5">
                                    <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></span>
                                    LIVE TRADING ACTIVE
                                </span>
                            </div>

                            <div className="flex items-center space-x-4">
                                <div className="text-xs text-slate-400 hidden md:block border border-slate-800 bg-slate-900 px-3 py-1.5 rounded-md">
                                    <span className="text-blue-400 font-mono">⚡ Scanning markets continuously...</span>
                                </div>
                                {triggeredMsg && (
                                    <span className="flex items-center text-xs text-emerald-400 font-medium animate-pulse">
                                        <CheckCircle2 className="w-4 h-4 mr-1" /> Cycle Queued!
                                    </span>
                                )}
                                <button
                                    onClick={async () => {
                                        if (window.confirm("Are you sure you want to PANIC SELL all open positions?")) {
                                            try {
                                                const { panicSell } = await import('./api/client');
                                                const res = await panicSell();
                                                alert(res.message || "Panic sell executed.");
                                            } catch (e) {
                                                alert("Panic sell failed.");
                                            }
                                        }
                                    }}
                                    className="flex items-center space-x-2 px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-all shadow-md shadow-red-600/20 active:scale-95 cursor-pointer mr-2"
                                >
                                    <span>Panic Sell All</span>
                                </button>
                                <button
                                    onClick={handleTrigger}
                                    disabled={triggering}
                                    className="flex items-center space-x-2 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white rounded-lg text-sm font-medium transition-all shadow-md shadow-blue-600/20 active:scale-95 cursor-pointer"
                                >
                                    <Play className="w-4 h-4 fill-current" />
                                    <span>{triggering ? "Triggering..." : "Force Cycle"}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </nav>

                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <Routes>
                        <Route path="/" element={<DashboardSummary />} />
                        <Route path="/model/:modelName" element={<ModelView />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
};

export default App;
