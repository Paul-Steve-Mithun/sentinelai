import { Link, useLocation } from 'react-router-dom';
import { Shield, Users, AlertTriangle, BarChart3 } from 'lucide-react';

export default function Navbar() {
    const location = useLocation();

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="glass border-b border-white/10">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    <Link to="/" className="flex items-center space-x-3">
                        <Shield className="w-8 h-8 text-blue-500" />
                        <span className="text-2xl font-bold gradient-text">SentinelAI</span>
                    </Link>

                    <div className="flex space-x-1">
                        <NavLink to="/" icon={BarChart3} label="Dashboard" active={isActive('/')} />
                        <NavLink to="/employees" icon={Users} label="Employees" active={isActive('/employees')} />
                    </div>
                </div>
            </div>
        </nav>
    );
}

function NavLink({ to, icon: Icon, label, active }) {
    return (
        <Link
            to={to}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${active
                    ? 'bg-blue-500/20 text-blue-400'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                }`}
        >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{label}</span>
        </Link>
    );
}
