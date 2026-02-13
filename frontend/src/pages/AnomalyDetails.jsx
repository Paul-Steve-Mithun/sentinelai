import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Shield, CheckCircle, XCircle } from 'lucide-react';
import RiskBadge from '../components/RiskBadge';
import ShapChart from '../components/ShapChart';
import { getAnomaly, getAnomalyMitre, getAnomalyMitigation, resolveAnomaly } from '../services/api';

export default function AnomalyDetails() {
    const { id } = useParams();
    const [anomaly, setAnomaly] = useState(null);
    const [mitreMappings, setMitreMappings] = useState([]);
    const [mitigations, setMitigations] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAnomalyData();
    }, [id]);

    const loadAnomalyData = async () => {
        try {
            const [anomRes, mitreRes, mitigRes] = await Promise.all([
                getAnomaly(id),
                getAnomalyMitre(id),
                getAnomalyMitigation(id)
            ]);
            setAnomaly(anomRes.data);
            setMitreMappings(mitreRes.data);
            setMitigations(mitigRes.data);
        } catch (error) {
            console.error('Error loading anomaly:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleResolve = async (status) => {
        try {
            await resolveAnomaly(id, {
                resolved_by: 'Security Team',
                resolution_notes: `Marked as ${status}`,
                status
            });
            loadAnomalyData();
        } catch (error) {
            console.error('Error resolving anomaly:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="pulse-slow text-blue-500 text-xl">Loading anomaly details...</div>
            </div>
        );
    }

    if (!anomaly) {
        return <div className="text-center py-12 text-gray-400">Anomaly not found</div>;
    }

    return (
        <div className="space-y-6 fade-in">
            <Link to="/" className="flex items-center space-x-2 text-gray-400 hover:text-white transition">
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Dashboard</span>
            </Link>

            {/* Anomaly Header */}
            <div className="glass rounded-xl p-6">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Anomaly Details</h1>
                        <p className="text-gray-400">Detected: {new Date(anomaly.detected_at).toLocaleString()}</p>
                    </div>
                    <RiskBadge level={anomaly.risk_level} score={anomaly.risk_score} />
                </div>

                <div className="bg-white/5 rounded-lg p-4 mb-4">
                    <p className="text-white text-lg">{anomaly.description}</p>
                    <p className="text-gray-400 mt-2">Type: <span className="text-white">{anomaly.anomaly_type}</span></p>
                </div>

                {anomaly.status === 'open' && (
                    <div className="flex space-x-3">
                        <button
                            onClick={() => handleResolve('resolved')}
                            className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition"
                        >
                            <CheckCircle className="w-5 h-5" />
                            <span>Mark Resolved</span>
                        </button>
                        <button
                            onClick={() => handleResolve('false_positive')}
                            className="flex items-center space-x-2 px-4 py-2 bg-gray-500/20 text-gray-400 rounded-lg hover:bg-gray-500/30 transition"
                        >
                            <XCircle className="w-5 h-5" />
                            <span>False Positive</span>
                        </button>
                    </div>
                )}
            </div>

            {/* SHAP Explanation */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-6">Explanation (SHAP Analysis)</h2>
                <ShapChart shapValues={anomaly.shap_values} topFeatures={anomaly.top_features} />
            </div>

            {/* MITRE ATT&CK Mapping */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-6">MITRE ATT&CK Mapping</h2>
                {mitreMappings.length === 0 ? (
                    <p className="text-gray-400">No MITRE mappings available</p>
                ) : (
                    <div className="space-y-4">
                        {mitreMappings.map((mapping) => (
                            <div key={mapping.id} className="bg-white/5 rounded-lg p-4">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center space-x-3">
                                        <Shield className="w-5 h-5 text-red-400" />
                                        <div>
                                            <h3 className="text-white font-semibold">{mapping.technique_id}: {mapping.technique_name}</h3>
                                            <p className="text-sm text-gray-400">{mapping.tactic}</p>
                                        </div>
                                    </div>
                                    <span className="text-sm text-gray-400">
                                        Confidence: {(mapping.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <p className="text-gray-300 text-sm">{mapping.description}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Mitigation Strategies */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-2xl font-bold text-white mb-6">Mitigation Strategies</h2>
                {mitigations.length === 0 ? (
                    <p className="text-gray-400">No mitigation strategies available</p>
                ) : (
                    <div className="space-y-3">
                        {mitigations.map((strategy) => (
                            <div
                                key={strategy.id}
                                className={`p-4 rounded-lg border ${strategy.priority === 1
                                        ? 'bg-red-500/10 border-red-500/50'
                                        : strategy.priority === 2
                                            ? 'bg-orange-500/10 border-orange-500/50'
                                            : 'bg-blue-500/10 border-blue-500/50'
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-3 mb-2">
                                            <span className="text-xs font-semibold px-2 py-1 rounded bg-white/10 text-white">
                                                Priority {strategy.priority}
                                            </span>
                                            <span className="text-xs text-gray-400 uppercase">{strategy.category}</span>
                                        </div>
                                        <h3 className="text-white font-semibold mb-1">{strategy.action}</h3>
                                        <p className="text-gray-300 text-sm">{strategy.description}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
