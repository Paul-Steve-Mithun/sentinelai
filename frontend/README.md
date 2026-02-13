# SentinelAI - Insider Threat Detection System

A comprehensive behavioral-based insider threat detection system using machine learning anomaly detection.

## Features

- **Behavioral Fingerprinting**: Creates personalized baselines for each employee
- **ML Anomaly Detection**: Uses Isolation Forest and K-Means clustering
- **SHAP Explainability**: Interpretable predictions showing which features contributed to detection
- **MITRE ATT&CK Mapping**: Maps detected anomalies to attack techniques
- **Automated Mitigation**: Provides prioritized, actionable recommendations
- **Real-time Monitoring**: Live dashboard with risk scoring

## Tech Stack

- **Frontend**: React + Tailwind CSS + Recharts
- **Backend**: FastAPI + SQLite
- **ML**: scikit-learn + SHAP + pandas
- **Monitoring**: Linux scripts (optional)

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Generate demo data
python scripts/data_generator.py

# Train ML model
# Start the server first, then call the training endpoint
uvicorn main:app --reload --port 8000

# In another terminal, train the model:
curl -X POST http://localhost:8000/api/ml/train
```

### 2. Frontend Setup

```bash
# In the root directory
npm install

# Start development server
npm run dev
```

### 3. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

1. **View Dashboard**: See overall statistics, anomaly timeline, and top threats
2. **Monitor Employees**: Browse all employees and their risk levels
3. **View Employee Profiles**: See behavioral fingerprints and anomaly history
4. **Investigate Anomalies**: View SHAP explanations, MITRE mappings, and mitigation strategies

## Project Structure

```
sentinelai/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── ml/                     # ML pipeline
│   │   ├── feature_engineering.py
│   │   ├── anomaly_detector.py
│   │   ├── explainability.py
│   │   ├── mitre_mapper.py
│   │   └── mitigation_engine.py
│   ├── routes/                 # API endpoints
│   │   ├── employees.py
│   │   ├── events.py
│   │   ├── anomalies.py
│   │   ├── dashboard.py
│   │   └── ml_ops.py
│   └── scripts/
│       └── data_generator.py   # Demo data generator
├── src/
│   ├── components/             # React components
│   ├── pages/                  # Page components
│   ├── services/               # API service layer
│   └── App.jsx                 # Main app component
└── package.json
```

## API Endpoints

### Employees
- `GET /api/employees` - List all employees
- `GET /api/employees/{id}` - Get employee details
- `GET /api/employees/{id}/profile` - Get behavioral profile

### Events
- `POST /api/events` - Submit security event
- `GET /api/events/{employee_id}` - Get employee events

### Anomalies
- `GET /api/anomalies` - List anomalies (with filters)
- `GET /api/anomalies/{id}` - Get anomaly details
- `GET /api/anomalies/{id}/mitre` - Get MITRE mappings
- `GET /api/anomalies/{id}/mitigation` - Get mitigation strategies
- `POST /api/anomalies/{id}/resolve` - Resolve anomaly

### Dashboard
- `GET /api/dashboard/stats` - Overall statistics
- `GET /api/dashboard/risk-distribution` - Risk distribution
- `GET /api/dashboard/top-threats` - Top threats
- `GET /api/dashboard/timeline` - Anomaly timeline

### ML Operations
- `POST /api/ml/train` - Train/retrain model
- `GET /api/ml/model-info` - Get model metadata
- `POST /api/ml/predict` - Manual prediction

## Behavioral Features

The system monitors 14 behavioral features:

1. **Login Patterns**: Average login hour, time variability
2. **Location**: Unique locations, deviation from baseline
3. **Network**: Port usage, unusual ports
4. **File Access**: Access rate, sensitive file access
5. **Privilege**: Escalation frequency
6. **Firewall**: Configuration changes
7. **Network Activity**: Volume of network events
8. **Failed Logins**: Failed authentication attempts
9. **Time Patterns**: Weekday vs weekend, night activity

## MITRE ATT&CK Techniques Covered

- T1078: Valid Accounts
- T1021: Remote Services
- T1068: Exploitation for Privilege Escalation
- T1048: Exfiltration Over Alternative Protocol
- T1562: Impair Defenses
- T1530: Data from Cloud Storage
- T1110: Brute Force
- T1098: Account Manipulation

## License

MIT
