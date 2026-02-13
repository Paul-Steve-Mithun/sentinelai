import { useState, useEffect } from 'react';
import { Users, AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import StatCard from '../components/StatCard';
import RiskBadge from '../components/RiskBadge';
import { getDashboardStats, getRiskDistribution, getTopThreats, getAnomalyTimeline } from '../services/api';
import { Link } from 'react-router-dom';

const RISK_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e'
};

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [riskDist, setRiskDist] = useState(null);
    const [topThreats, setTopThreats] = useState([]);
    const [timeline, setTimeline] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            const [statsRes, riskRes, threatsRes, timelineRes] = await Promise.all([
                getDashboardStats(),
                getRiskDistribution(),
                getTopThreats(),
                getAnomalyTimeline(30)
            ]);

            setStats(statsRes.data);
            setRiskDist(riskRes.data);
            setTopThreats(threatsRes.data);
            setTimeline(timelineRes.data);
        } catch (error) {
            console.error('Error loading dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="pulse-slow text-blue-500 text-xl">Loading dashboard...</div>
            </div>
        );
    }

    const pieData = riskDist ? [
        { name: 'Critical', value: riskDist.critical, color: RISK_COLORS.critical },
        { name: 'High', value: riskDist.high, color: RISK_COLORS.high },
        { name: 'Medium', value: riskDist.medium, color: RISK_COLORS.medium },
        { name: 'Low', value: riskDist.low, color: RISK_COLORS.low }
    ] : [];

    return (
        <div className="space-y-8 fade-in">
            <div>
                <h1 className="text-4xl font-bold text-white mb-2">Threat Dashboard</h1>
                <p className="text-gray-400">Real-time insider threat detection and monitoring</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    icon={Users}
                    label="Total Employees"
                    value={stats?.total_employees || 0}
                    gradient="bg-gradient-to-br from-blue-500/20 to-blue-600/20"
                />
                <StatCard
                    icon={AlertTriangle}
                    label="Active Threats"
                    value={stats?.active_threats || 0}
                    trend={5}
                    gradient="bg-gradient-to-br from-red-500/20 to-red-600/20"
                />
                <StatCard
                    icon={Activity}
                    label="Total Anomalies"
                    value={stats?.total_anomalies || 0}
                    gradient="bg-gradient-to-br from-purple-500/20 to-purple-600/20"
                />
                <StatCard
                    icon={TrendingUp}
                    label="Avg Risk Score"
                    value={stats?.avg_risk_score?.toFixed(1) || '0.0'}
                    gradient="bg-gradient-to-br from-orange-500/20 to-orange-600/20"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Timeline Chart */}
                <div className="glass rounded-xl p-6">
                    <h2 className="text-xl font-bold text-white mb-4">Anomaly Timeline (30 Days)</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={timeline}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="date" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1f2937',
                                    border: '1px solid #374151',
                                    borderRadius: '8px'
                                }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="critical" stroke={RISK_COLORS.critical} strokeWidth={2} />
                            <Line type="monotone" dataKey="high" stroke={RISK_COLORS.high} strokeWidth={2} />
                            <Line type="monotone" dataKey="medium" stroke={RISK_COLORS.medium} strokeWidth={2} />
                            <Line type="monotone" dataKey="low" stroke={RISK_COLORS.low} strokeWidth={2} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Risk Distribution */}
                <div className="glass rounded-xl p-6">
                    <h2 className="text-xl font-bold text-white mb-4">Risk Distribution</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={pieData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, value }) => `${name}: ${value}`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Top Threats Table */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-4">Top Threats</h2>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/10">
                                <th className="text-left py-3 px-4 text-gray-400 font-medium">Employee</th>
                                <th className="text-left py-3 px-4 text-gray-400 font-medium">Risk Score</th>
                                <th className="text-left py-3 px-4 text-gray-400 font-medium">Anomalies</th>
                                <th className="text-left py-3 px-4 text-gray-400 font-medium">Latest Activity</th>
                                <th className="text-left py-3 px-4 text-gray-400 font-medium">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {topThreats.map((threat) => (
                                <tr key={threat.employee_id} className="border-b border-white/5 hover:bg-white/5 transition">
                                    <td className="py-3 px-4 text-white">{threat.employee_name}</td>
                                    <td className="py-3 px-4">
                                        <RiskBadge
                                            level={threat.risk_score >= 80 ? 'critical' : threat.risk_score >= 60 ? 'high' : threat.risk_score >= 40 ? 'medium' : 'low'}
                                            score={threat.risk_score}
                                        />
                                    </td>
                                    <td className="py-3 px-4 text-white">{threat.anomaly_count}</td>
                                    <td className="py-3 px-4 text-gray-400">
                                        {new Date(threat.latest_anomaly).toLocaleDateString()}
                                    </td>
                                    <td className="py-3 px-4">
                                        <Link
                                            to={`/employees/${threat.employee_id}`}
                                            className="text-blue-400 hover:text-blue-300 transition"
                                        >
                                            View Profile →
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
