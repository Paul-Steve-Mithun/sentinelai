import { useState, useEffect } from 'react';
import { Search, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import RiskBadge from '../components/RiskBadge';
import { getEmployees, getAnomalies } from '../services/api';

export default function EmployeeMonitoring() {
    const [employees, setEmployees] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [empRes, anomRes] = await Promise.all([
                getEmployees(),
                getAnomalies({ status: 'open' })
            ]);
            setEmployees(empRes.data);
            setAnomalies(anomRes.data);
        } catch (error) {
            console.error('Error loading employees:', error);
        } finally {
            setLoading(false);
        }
    };

    const getEmployeeRisk = (employeeId) => {
        const empAnomalies = anomalies.filter(a => a.employee_id === employeeId);
        if (empAnomalies.length === 0) return { level: 'low', score: 0, count: 0 };

        const maxRisk = Math.max(...empAnomalies.map(a => a.risk_score));
        const level = maxRisk >= 80 ? 'critical' : maxRisk >= 60 ? 'high' : maxRisk >= 40 ? 'medium' : 'low';

        return { level, score: maxRisk, count: empAnomalies.length };
    };

    const filteredEmployees = employees.filter(emp =>
        emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.department.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="pulse-slow text-blue-500 text-xl">Loading employees...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6 fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-white mb-2">Employee Monitoring</h1>
                    <p className="text-gray-400">Monitor behavioral patterns and detect anomalies</p>
                </div>
            </div>

            {/* Search Bar */}
            <div className="glass rounded-xl p-4">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Search employees by name, email, or department..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 transition"
                    />
                </div>
            </div>

            {/* Employee Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredEmployees.map((employee) => {
                    const risk = getEmployeeRisk(employee._id);

                    return (
                        <Link
                            key={employee._id}
                            to={`/employees/${employee._id}`}
                            className="glass rounded-xl p-6 card-hover"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center space-x-3">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                                        <User className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">{employee.name}</h3>
                                        <p className="text-sm text-gray-400">{employee.employee_id}</p>
                                    </div>
                                </div>
                                <RiskBadge level={risk.level} />
                            </div>

                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Email:</span>
                                    <span className="text-white">{employee.email}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Department:</span>
                                    <span className="text-white">{employee.department}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Role:</span>
                                    <span className="text-white">{employee.role}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Location:</span>
                                    <span className="text-white">{employee.baseline_location}</span>
                                </div>
                                {risk.count > 0 && (
                                    <div className="flex justify-between pt-2 border-t border-white/10">
                                        <span className="text-gray-400">Active Anomalies:</span>
                                        <span className="text-red-400 font-semibold">{risk.count}</span>
                                    </div>
                                )}
                            </div>
                        </Link>
                    );
                })}
            </div>

            {filteredEmployees.length === 0 && (
                <div className="text-center py-12 text-gray-400">
                    No employees found matching your search.
                </div>
            )}
        </div>
    );
}
