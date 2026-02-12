import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import EmployeeMonitoring from './pages/EmployeeMonitoring';
import EmployeeProfile from './pages/EmployeeProfile';
import AnomalyDetails from './pages/AnomalyDetails';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/employees" element={<EmployeeMonitoring />} />
            <Route path="/employees/:id" element={<EmployeeProfile />} />
            <Route path="/anomalies/:id" element={<AnomalyDetails />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
