import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, User, MapPin, Mail, Briefcase } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import RiskBadge from '../components/RiskBadge';
import { getEmployee, getEmployeeProfile, getEmployeeAnomalies } from '../services/api';

export default function EmployeeProfile() {
    const { id } = useParams();
    const [employee, setEmployee] = useState(null);
    const [profile, setProfile] = useState(null);
    const [anomalies, setAnomalies] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadEmployeeData();
    }, [id]);

    const loadEmployeeData = async () => {
        try {
            const [empRes, profRes, anomRes] = await Promise.all([
                getEmployee(id),
                getEmployeeProfile(id),
                getEmployeeAnomalies(id)
            ]);
            setEmployee(empRes.data);
            setProfile(profRes.data);
            setAnomalies(anomRes.data);
        } catch (error) {
            console.error('Error loading employee:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="pulse-slow text-blue-500 text-xl">Loading profile...</div>
            </div>
        );
    }

    if (!employee) {
        return (
            <div className="text-center py-12 text-gray-400">
                Employee not found
            </div>
        );
    }

    const radarData = profile ? [
        { metric: 'Login Pattern', value: Math.min(profile.login_hour_std * 10, 100) },
        { metric: 'Location Variance', value: profile.avg_location_distance * 100 },
        { metric: 'Port Usage', value: Math.min(profile.unique_ports_count * 10, 100) },
        { metric: 'File Access', value: Math.min(profile.file_access_rate * 5, 100) },
        { metric: 'Privilege Use', value: Math.min(profile.privilege_escalation_rate * 20, 100) },
        { metric: 'Network Activity', value: Math.min(profile.network_activity_volume * 5, 100) }
    ] : [];

    return (
        <div className="space-y-6 fade-in">
            <Link to="/employees" className="flex items-center space-x-2 text-gray-400 hover:text-white transition">
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Employees</span>
            </Link>

            {/* Employee Header */}
            <div className="glass rounded-xl p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-4">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                            <User className="w-10 h-10 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-white">{employee.name}</h1>
                            <p className="text-gray-400">{employee.employee_id}</p>
                        </div>
                    </div>
                    {anomalies.length > 0 && (
                        <RiskBadge
                            level={anomalies[0].risk_level}
                            score={anomalies[0].risk_score}
                        />
                    )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    <div className="flex items-center space-x-3">
                        <Mail className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-400">Email</p>
                            <p className="text-white">{employee.email}</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        <Briefcase className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-400">Department</p>
                            <p className="text-white">{employee.department} - {employee.role}</p>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3">
                        <MapPin className="w-5 h-5 text-gray-400" />
                        <div>
                            <p className="text-sm text-gray-400">Location</p>
                            <p className="text-white">{employee.baseline_location}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Behavioral Profile */}
            {profile && (
                <div className="glass rounded-xl p-6">
                    <h2 className="text-2xl font-bold text-white mb-6">Behavioral Fingerprint</h2>
                    <ResponsiveContainer width="100%" height={400}>
                        <RadarChart data={radarData}>
                            <PolarGrid stroke="#374151" />
                            <PolarAngleAxis dataKey="metric" stroke="#9ca3af" />
                            <PolarRadiusAxis stroke="#9ca3af" />
                            <Radar name="Behavior" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Anomaly History */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-6">Anomaly History</h2>
                {anomalies.length === 0 ? (
                    <p className="text-gray-400 text-center py-8">No anomalies detected</p>
                ) : (
                    <div className="space-y-4">
                        {anomalies.map((anomaly) => (
                            <Link
                                key={anomaly.id}
                                to={`/anomalies/${anomaly.id}`}
                                className="block glass p-4 rounded-lg hover:bg-white/10 transition"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-3 mb-2">
                                            <RiskBadge level={anomaly.risk_level} score={anomaly.risk_score} />
                                            <span className="text-sm text-gray-400">
                                                {new Date(anomaly.detected_at).toLocaleString()}
                                            </span>
                                        </div>
                                        <p className="text-white">{anomaly.description}</p>
                                        <p className="text-sm text-gray-400 mt-1">Type: {anomaly.anomaly_type}</p>
                                    </div>
                                    <span className="text-blue-400">View Details →</span>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
