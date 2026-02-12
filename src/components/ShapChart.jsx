import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function ShapChart({ shapValues, topFeatures }) {
    if (!topFeatures || topFeatures.length === 0) {
        return <div className="text-gray-400 text-center py-8">No explanation data available</div>;
    }

    const data = topFeatures.map(f => ({
        name: f.feature_display,
        value: Math.abs(f.shap_value),
        impact: f.shap_value > 0 ? 'positive' : 'negative',
        description: f.description
    }));

    return (
        <div className="space-y-4">
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data} layout="vertical" margin={{ left: 120, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis type="number" stroke="#9ca3af" />
                    <YAxis type="category" dataKey="name" stroke="#9ca3af" width={110} />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: '#1f2937',
                            border: '1px solid #374151',
                            borderRadius: '8px',
                            color: '#fff'
                        }}
                    />
                    <Bar
                        dataKey="value"
                        fill="#3b82f6"
                        radius={[0, 4, 4, 0]}
                    />
                </BarChart>
            </ResponsiveContainer>

            <div className="space-y-2">
                {topFeatures.map((feature, idx) => (
                    <div key={idx} className="glass p-3 rounded-lg">
                        <p className="text-sm text-gray-300">{feature.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
