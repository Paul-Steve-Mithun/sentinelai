export default function StatCard({ icon: Icon, label, value, trend, gradient }) {
    return (
        <div className={`glass rounded-xl p-6 card-hover ${gradient}`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-gray-400 text-sm font-medium">{label}</p>
                    <p className="text-3xl font-bold text-white mt-2">{value}</p>
                    {trend && (
                        <p className={`text-sm mt-2 ${trend > 0 ? 'text-red-400' : 'text-green-400'}`}>
                            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last week
                        </p>
                    )}
                </div>
                <div className="p-3 rounded-lg bg-white/10">
                    <Icon className="w-8 h-8 text-white" />
                </div>
            </div>
        </div>
    );
}
