export default function RiskBadge({ level, score }) {
    const getStyles = () => {
        switch (level) {
            case 'critical':
                return 'risk-critical border';
            case 'high':
                return 'risk-high border';
            case 'medium':
                return 'risk-medium border';
            case 'low':
                return 'risk-low border';
            default:
                return 'bg-gray-500/20 text-gray-400 border-gray-500/50 border';
        }
    };

    return (
        <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${getStyles()}`}>
            {level} {score && `(${score})`}
        </span>
    );
}
