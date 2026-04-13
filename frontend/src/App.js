import React, { useState, useEffect, useCallback, createContext, useContext, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate, Navigate, useParams } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import {
  Brain,
  BarChart3,
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronRight,
  Plus,
  Download,
  Bell,
  BellOff,
  Target,
  FileText,
  TrendingUp,
  Users,
  Beaker,
  ListTodo,
  Menu,
  X,
  Edit2,
  Trash2,
  ArrowRight,
  LogOut,
  Lock,
  ClipboardList,
  Info,
  Activity,
  Bookmark,
  Timer,
  HelpCircle,
  Copy,
  Share2,
  ExternalLink,
  FileDown,
  Shield,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const RESEARCHER_PASSWORD = "pmresearch2026";

// ========================
// Context
// ========================

const AuthContext = createContext(null);

const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem("researcher_auth") === "true";
  });

  const login = (password) => {
    if (password === RESEARCHER_PASSWORD) {
      localStorage.setItem("researcher_auth", "true");
      setIsAuthenticated(true);
      return true;
    }
    return false;
  };

  const logout = () => {
    localStorage.removeItem("researcher_auth");
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// ========================
// API Functions
// ========================

const api = {
  getExperiments: () => axios.get(`${API}/experiments`),
  createExperiment: (data) => axios.post(`${API}/experiments`, data),
  getExperiment: (id) => axios.get(`${API}/experiments/${id}`),
  deleteExperiment: (id) => axios.delete(`${API}/experiments/${id}`),
  joinExperimentByCode: (code) => axios.get(`${API}/experiments/join/${code}`),
  getSessions: (params) => axios.get(`${API}/sessions`, { params }),
  createSession: (data) => axios.post(`${API}/sessions`, data),
  getSession: (id) => axios.get(`${API}/sessions/${id}`),
  startSession: (id) => axios.post(`${API}/sessions/${id}/start`),
  completeSession: (id) => axios.post(`${API}/sessions/${id}/complete`),
  startBlackout: (id) => axios.post(`${API}/sessions/${id}/start-blackout`),
  recordNotification: (id, data) => axios.post(`${API}/sessions/${id}/notification`, data),
  recordOffloadingEvent: (id, data) => axios.post(`${API}/sessions/${id}/offloading-event`, data),
  recordRecallProbe: (id, data) => axios.post(`${API}/sessions/${id}/recall-probe`, data),
  updateStrategyMetrics: (id, params) => axios.put(`${API}/sessions/${id}/strategy-metrics`, null, { params }),
  getParticipants: (params) => axios.get(`${API}/participants`, { params }),
  createParticipant: (data) => axios.post(`${API}/participants`, data),
  updateParticipantDemographics: (id, data) => axios.put(`${API}/participants/${id}/demographics`, data),
  getTasks: (params) => axios.get(`${API}/tasks`, { params }),
  createTask: (data) => axios.post(`${API}/tasks`, data),
  updateTask: (id, data) => axios.put(`${API}/tasks/${id}`, data),
  deleteTask: (id) => axios.delete(`${API}/tasks/${id}`),
  getWeeklyReports: () => axios.get(`${API}/weekly-reports`),
  createWeeklyReport: (data) => axios.post(`${API}/weekly-reports`, data),
  getOverviewAnalytics: () => axios.get(`${API}/analytics/overview`),
  getExperimentAnalytics: (id) => axios.get(`${API}/analytics/experiments/${id}`),
  getProgressAnalytics: () => axios.get(`${API}/analytics/progress`),
  getOffloadingComparison: () => axios.get(`${API}/analytics/offloading-comparison`),
  exportSessions: (experimentId, format) => axios.get(`${API}/export/sessions`, { params: { experiment_id: experimentId, format } }),
  exportFullData: () => axios.get(`${API}/export/full-research-data`),
  exportValidatedData: () => axios.get(`${API}/export/validated-research-data`),
  exportTasks: (format) => axios.get(`${API}/export/tasks`, { params: { format } }),
  seedData: () => axios.post(`${API}/seed`),
};

// ========================
// Shared Components
// ========================

const StatusBadge = ({ status }) => {
  const styles = {
    completed: "badge-success",
    active: "badge-info",
    pending: "badge-neutral",
    blackout: "badge-warning",
    not_started: "badge-neutral",
    in_progress: "badge-info",
    blocked: "badge-error",
  };
  return (
    <span className={`badge ${styles[status] || "badge-neutral"}`} data-testid={`status-${status}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
};

const PriorityBadge = ({ priority }) => (
  <span className={`badge priority-${priority}`} data-testid={`priority-${priority}`}>
    {priority.toUpperCase()}
  </span>
);

const StrategyBadge = ({ strategy }) => (
  <span className={`badge strategy-${strategy}`} data-testid={`strategy-${strategy}`}>
    {strategy.replace(/_/g, " ")}
  </span>
);

const Button = ({ children, variant = "primary", size = "md", className = "", ...props }) => {
  const sizes = { sm: "px-3 py-1.5 text-sm", md: "px-4 py-2 text-sm", lg: "px-6 py-2.5" };
  const variants = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "bg-transparent hover:bg-gray-100 text-gray-700",
    danger: "bg-red-600 text-white hover:bg-red-700",
    success: "bg-green-600 text-white hover:bg-green-700",
    warning: "bg-amber-500 text-white hover:bg-amber-600",
  };
  return (
    <button className={`btn ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
};

const Input = ({ label, error, className = "", ...props }) => (
  <div className={className}>
    {label && <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>}
    <input className="input" {...props} />
    {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
  </div>
);

const Select = ({ label, options, className = "", ...props }) => (
  <div className={className}>
    {label && <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>}
    <select className="select" {...props}>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  </div>
);

const Textarea = ({ label, className = "", ...props }) => (
  <div className={className}>
    {label && <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>}
    <textarea className="textarea" {...props} />
  </div>
);

const Modal = ({ isOpen, onClose, title, children, size = "md" }) => {
  if (!isOpen) return null;
  const sizes = { sm: "max-w-md", md: "max-w-lg", lg: "max-w-2xl" };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="modal">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div className={`relative z-10 bg-white rounded-lg shadow-xl w-full ${sizes[size]} max-h-[90vh] overflow-auto animate-fadeIn`}>
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded" data-testid="modal-close">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const Card = ({ children, className = "", hover = false }) => (
  <div className={`card ${hover ? "card-hover cursor-pointer" : ""} ${className}`}>
    {children}
  </div>
);

const EmptyState = ({ icon: Icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
      <Icon className="w-6 h-6 text-gray-400" />
    </div>
    <h3 className="font-medium text-gray-900 mb-1">{title}</h3>
    <p className="text-sm text-gray-500 mb-4 max-w-sm">{description}</p>
    {action}
  </div>
);

// ========================
// PARTICIPANT INTERFACE
// ========================

const ParticipantLanding = () => {
  const navigate = useNavigate();
  const [studyCode, setStudyCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleJoinStudy = async (e) => {
    e.preventDefault();
    if (!studyCode.trim()) {
      setError("Please enter a study code");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await api.joinExperimentByCode(studyCode.trim());
      sessionStorage.setItem("study_code", studyCode.trim());
      sessionStorage.setItem("selected_experiment", JSON.stringify(response.data));
      navigate(`/participate/consent`);
    } catch (err) {
      const msg = err.response?.data?.detail || "Invalid study code. Please check and try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="participant-view">
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">PM Research Lab</h1>
              <p className="text-xs text-gray-500">Prospective Memory Study</p>
            </div>
          </div>
          <Link to="/researcher/login" className="text-sm text-gray-500 hover:text-gray-700">
            Researcher Access
          </Link>
        </div>
      </header>

      <div className="hero-gradient text-white py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-3xl md:text-4xl font-bold mb-4 animate-fadeInUp">
            Prospective Memory & Digital Notifications Study
          </h1>
          <p className="text-lg text-white/90 max-w-2xl mx-auto animate-fadeInUp stagger-1">
            Investigating how automated reminders influence our ability to remember future intentions
          </p>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="grid md:grid-cols-2 gap-8">
          <Card className="p-6 animate-fadeIn">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-teal-100 flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-teal-700" />
              </div>
              <h2 className="text-xl font-semibold">Join a Study</h2>
            </div>
            <p className="text-gray-600 mb-6">
              Enter the study code provided by your researcher to begin.
            </p>
            <form onSubmit={handleJoinStudy}>
              <Input
                placeholder="Enter study code (e.g., JIT-2026-A)"
                value={studyCode}
                onChange={(e) => { setStudyCode(e.target.value); setError(""); }}
                className="mb-3"
                data-testid="study-code-input"
              />
              {error && <p className="text-sm text-red-600 mb-3" data-testid="study-code-error">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading} data-testid="join-study-btn">
                {loading ? "Verifying..." : "Continue"} {!loading && <ArrowRight className="w-4 h-4 ml-2" />}
              </Button>
            </form>
          </Card>

          <Card className="p-6 animate-fadeIn stagger-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Info className="w-5 h-5 text-blue-700" />
              </div>
              <h2 className="text-xl font-semibold">About This Study</h2>
            </div>
            <div className="space-y-4 text-gray-600">
              <p>
                This research examines how digital notification systems affect <strong>prospective memory</strong>—our ability to remember intended actions.
              </p>
              <p>
                You'll experience a simulated medication reminder scenario, make choices about remembering vs. setting reminders, and complete memory tests. Takes approximately <strong>10-15 minutes</strong>.
              </p>
            </div>
          </Card>
        </div>

        <div className="mt-12">
          <h2 className="text-xl font-semibold text-center mb-8">Key Research Concepts</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="p-5 animate-fadeIn stagger-2">
              <div className="w-8 h-8 rounded bg-violet-100 flex items-center justify-center mb-3">
                <Brain className="w-4 h-4 text-violet-700" />
              </div>
              <h3 className="font-medium mb-2">Prospective Memory</h3>
              <p className="text-sm text-gray-600">
                Remembering to perform an intended action at the right time in the future.
              </p>
            </Card>
            <Card className="p-5 animate-fadeIn stagger-3">
              <div className="w-8 h-8 rounded bg-amber-100 flex items-center justify-center mb-3">
                <Activity className="w-4 h-4 text-amber-700" />
              </div>
              <h3 className="font-medium mb-2">Cognitive Offloading</h3>
              <p className="text-sm text-gray-600">
                Using external tools (like phone reminders) to reduce mental demand.
              </p>
            </Card>
            <Card className="p-5 animate-fadeIn stagger-4">
              <div className="w-8 h-8 rounded bg-teal-100 flex items-center justify-center mb-3">
                <Bell className="w-4 h-4 text-teal-700" />
              </div>
              <h3 className="font-medium mb-2">Notification Strategies</h3>
              <p className="text-sm text-gray-600">
                Different timing and frequency patterns for digital reminders.
              </p>
            </Card>
          </div>
        </div>
      </main>

      <footer className="border-t bg-white mt-12">
        <div className="max-w-4xl mx-auto px-6 py-6 text-center text-sm text-gray-500">
          <p>All data is anonymized and used for research purposes only.</p>
        </div>
      </footer>
    </div>
  );
};

const StudyJoinRedirect = () => {
  const { shareCode } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const joinStudy = async () => {
      try {
        const response = await api.joinExperimentByCode(shareCode);
        sessionStorage.setItem("study_code", shareCode);
        sessionStorage.setItem("selected_experiment", JSON.stringify(response.data));
        navigate("/participate/consent", { replace: true });
      } catch (err) {
        setError(err.response?.data?.detail || "Invalid study link. Please check the URL.");
        setLoading(false);
      }
    };
    joinStudy();
  }, [shareCode, navigate]);

  if (loading) {
    return (
      <div className="participant-view min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-lg bg-[#1E3A5F] flex items-center justify-center mx-auto mb-4 animate-pulse-dot">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <p className="text-gray-600">Joining study...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="participant-view min-h-screen flex items-center justify-center p-4">
      <Card className="p-8 max-w-md w-full text-center">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-6 h-6 text-red-600" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Invalid Study Link</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <Button onClick={() => navigate("/")} variant="secondary" className="w-full" data-testid="back-home-btn">
          Go to Home
        </Button>
      </Card>
    </div>
  );
};

const ParticipantConsent = () => {
  const navigate = useNavigate();
  const [agreed, setAgreed] = useState(false);

  const handleContinue = () => {
    if (agreed) {
      sessionStorage.setItem("consent_given", "true");
      sessionStorage.setItem("consent_timestamp", new Date().toISOString());
      navigate("/participate/demographics");
    }
  };

  return (
    <div className="participant-view min-h-screen">
      <header className="bg-white border-b">
        <div className="max-w-2xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">PM Research Lab</h1>
            <p className="text-xs text-gray-500">Informed Consent</p>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-12">
        <Card className="p-8 animate-fadeIn">
          <h2 className="text-2xl font-semibold mb-6">Informed Consent</h2>
          
          <div className="prose prose-sm text-gray-600 mb-8 space-y-4">
            <p><strong>Purpose:</strong> This study investigates how digital notification systems affect prospective memory and cognitive offloading behavior.</p>
            
            <p><strong>Procedure:</strong> You will experience a simulated medication reminder scenario. When notifications appear, you'll choose whether to "remember" the information or "set a reminder." Later, you'll be tested on your recall.</p>
            
            <p><strong>Duration:</strong> Approximately 10-15 minutes.</p>
            
            <p><strong>Risks:</strong> This study involves minimal risk. You may experience mild mental effort during memory tests.</p>
            
            <p><strong>Confidentiality:</strong> All data is anonymized. No personally identifiable information is collected.</p>
            
            <p><strong>Voluntary Participation:</strong> Your participation is voluntary. You may withdraw at any time without penalty.</p>
          </div>

          <label className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-1 w-4 h-4 text-[#1E3A5F] border-gray-300 rounded focus:ring-[#1E3A5F]"
              data-testid="consent-checkbox"
            />
            <span className="text-sm text-gray-700">
              I have read and understood the above information. I voluntarily agree to participate in this research study.
            </span>
          </label>

          <div className="mt-6">
            <Button 
              onClick={handleContinue} 
              className="w-full" 
              disabled={!agreed}
              data-testid="consent-continue-btn"
            >
              Continue <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </Card>
      </main>
    </div>
  );
};

const ParticipantDemographics = () => {
  const navigate = useNavigate();
  const [demographics, setDemographics] = useState({
    age_group: "",
    education: "",
    tech_familiarity: "",
    memory_self_rating: "",
  });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!demographics.age_group) newErrors.age_group = "Required";
    if (!demographics.education) newErrors.education = "Required";
    if (!demographics.tech_familiarity) newErrors.tech_familiarity = "Required";
    if (!demographics.memory_self_rating) newErrors.memory_self_rating = "Required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      // Store demographics for later submission with participant creation
      sessionStorage.setItem("participant_demographics", JSON.stringify({
        age_group: demographics.age_group,
        education: demographics.education,
        tech_familiarity: demographics.tech_familiarity,
        memory_self_rating: parseInt(demographics.memory_self_rating),
      }));
      navigate("/participate/simulation");
    }
  };

  return (
    <div className="participant-view min-h-screen">
      <header className="bg-white border-b">
        <div className="max-w-2xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">PM Research Lab</h1>
            <p className="text-xs text-gray-500">Participant Information</p>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-12">
        <Card className="p-8 animate-fadeIn">
          <h2 className="text-2xl font-semibold mb-2">About You</h2>
          <p className="text-gray-600 mb-8">
            Please provide some basic information. All responses are anonymous and used for research analysis only.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Select
                label="Age Group *"
                value={demographics.age_group}
                onChange={(e) => setDemographics({ ...demographics, age_group: e.target.value })}
                options={[
                  { value: "", label: "Select your age group" },
                  { value: "18-24", label: "18-24" },
                  { value: "25-34", label: "25-34" },
                  { value: "35-44", label: "35-44" },
                  { value: "45-54", label: "45-54" },
                  { value: "55-64", label: "55-64" },
                  { value: "65+", label: "65 or older" },
                ]}
                data-testid="age-select"
              />
              {errors.age_group && <p className="text-sm text-red-600 mt-1">{errors.age_group}</p>}
            </div>

            <div>
              <Select
                label="Highest Education Level *"
                value={demographics.education}
                onChange={(e) => setDemographics({ ...demographics, education: e.target.value })}
                options={[
                  { value: "", label: "Select education level" },
                  { value: "high_school", label: "High School" },
                  { value: "some_college", label: "Some College" },
                  { value: "bachelors", label: "Bachelor's Degree" },
                  { value: "masters", label: "Master's Degree" },
                  { value: "doctorate", label: "Doctorate" },
                ]}
                data-testid="education-select"
              />
              {errors.education && <p className="text-sm text-red-600 mt-1">{errors.education}</p>}
            </div>

            <div>
              <Select
                label="How often do you use smartphone reminders? *"
                value={demographics.tech_familiarity}
                onChange={(e) => setDemographics({ ...demographics, tech_familiarity: e.target.value })}
                options={[
                  { value: "", label: "Select frequency" },
                  { value: "never", label: "Never" },
                  { value: "rarely", label: "Rarely (few times a month)" },
                  { value: "sometimes", label: "Sometimes (few times a week)" },
                  { value: "often", label: "Often (daily)" },
                  { value: "always", label: "Always (multiple times daily)" },
                ]}
                data-testid="tech-select"
              />
              {errors.tech_familiarity && <p className="text-sm text-red-600 mt-1">{errors.tech_familiarity}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                How would you rate your memory? * <span className="text-gray-500">(1 = Poor, 5 = Excellent)</span>
              </label>
              <div className="flex gap-4">
                {[1, 2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setDemographics({ ...demographics, memory_self_rating: String(num) })}
                    className={`flex-1 p-3 text-center rounded-lg border-2 cursor-pointer transition-colors ${
                      demographics.memory_self_rating === String(num)
                        ? "border-[#1E3A5F] bg-[#1E3A5F]/5 text-[#1E3A5F] font-medium"
                        : "border-gray-200 hover:border-gray-300 text-gray-700"
                    }`}
                    data-testid={`memory-rating-${num}`}
                  >
                    {num}
                  </button>
                ))}
              </div>
              {errors.memory_self_rating && <p className="text-sm text-red-600 mt-1">{errors.memory_self_rating}</p>}
            </div>

            <div className="pt-4">
              <Button type="submit" className="w-full" data-testid="continue-btn">
                Continue to Simulation <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
};

const ParticipantSimulation = () => {
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [phase, setPhase] = useState("intro");
  const [simulatedTime, setSimulatedTime] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [currentNotification, setCurrentNotification] = useState(null);
  const [notificationShownAt, setNotificationShownAt] = useState(null);
  const [recallProbe, setRecallProbe] = useState(null);
  const [probeShownAt, setProbeShownAt] = useState(null);
  const [probeAnswer, setProbeAnswer] = useState("");
  const [results, setResults] = useState({ 
    correct: 0, 
    total: 0, 
    rememberChoices: 0, 
    offloadChoices: 0,
    responseTimes: [],
    decisionTimes: []
  });
  const [session, setSession] = useState(null);
  const [participant, setParticipant] = useState(null);
  
  // Strategy-specific state
  const [currentInterval, setCurrentInterval] = useState(null);
  const [currentProminence, setCurrentProminence] = useState(1.0);
  const lastNotificationTime = useRef(0);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    try {
      // Check if a specific experiment was pre-selected via share link
      const storedExp = sessionStorage.getItem("selected_experiment");
      if (storedExp) {
        const parsed = JSON.parse(storedExp);
        setSelectedExperiment(parsed);
        setCurrentInterval(parsed.config.notification_frequency_minutes);
        // Also load all experiments for reference
        const response = await api.getExperiments();
        setExperiments(response.data.filter(e => e.is_active));
        return;
      }
      
      const response = await api.getExperiments();
      const activeExps = response.data.filter(e => e.is_active);
      setExperiments(activeExps);
      if (activeExps.length > 0) {
        setSelectedExperiment(activeExps[0]);
        setCurrentInterval(activeExps[0].config.notification_frequency_minutes);
      }
    } catch (error) {
      console.error("Failed to load experiments:", error);
    }
  };

  const startSimulation = async () => {
    if (!selectedExperiment) return;
    try {
      // Get stored demographics
      const demographicsStr = sessionStorage.getItem("participant_demographics");
      const demographics = demographicsStr ? JSON.parse(demographicsStr) : null;

      // Create participant with demographics
      const participantRes = await api.createParticipant({
        participant_code: `P${Date.now()}`,
        experiment_id: selectedExperiment.id,
        demographics: demographics,
      });
      setParticipant(participantRes.data);

      // Create and start session
      const sessionRes = await api.createSession({
        participant_id: participantRes.data.id,
        experiment_id: selectedExperiment.id,
      });
      await api.startSession(sessionRes.data.id);
      setSession(sessionRes.data);
      
      // Initialize strategy-specific values
      setCurrentInterval(selectedExperiment.config.notification_frequency_minutes);
      setCurrentProminence(1.0);
      
      setPhase("running");
      setSimulatedTime(0);
      lastNotificationTime.current = 0;
      
      toast.success("Simulation started!");
    } catch (error) {
      toast.error("Failed to start simulation");
      console.error(error);
    }
  };

  // Simulation timer with strategy-specific logic
  useEffect(() => {
    if (phase !== "running" && phase !== "blackout") return;
    if (!selectedExperiment) return;

    const interval = setInterval(() => {
      setSimulatedTime((prev) => {
        const newTime = prev + selectedExperiment.config.time_compression_factor / 60;
        const blackoutStart = selectedExperiment.config.total_duration_minutes - selectedExperiment.config.blackout_duration_minutes;

        // Check for blackout transition
        if (phase === "running" && newTime >= blackoutStart) {
          setPhase("blackout");
          setCurrentNotification(null);
          triggerRecallProbe();
          if (session) {
            api.startBlackout(session.id);
            // Save final strategy metrics
            api.updateStrategyMetrics(session.id, {
              scaffolded_interval: currentInterval,
              faded_prominence: currentProminence
            });
          }
        }

        // Check for completion
        if (newTime >= selectedExperiment.config.total_duration_minutes) {
          setPhase("complete");
          if (session) api.completeSession(session.id);
        }

        // Trigger notifications (strategy-specific)
        if (phase === "running" && selectedExperiment.config.notification_strategy !== "control") {
          const timeSinceLastNotification = newTime - lastNotificationTime.current;
          
          // Use current interval (which changes for scaffolded strategy)
          if (currentInterval > 0 && timeSinceLastNotification >= currentInterval) {
            lastNotificationTime.current = newTime;
            triggerNotification(notifications.length + 1, newTime);
          }
        }

        return newTime;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [phase, selectedExperiment, session, currentInterval, notifications.length]);

  const triggerNotification = (count, time) => {
    const doseNum = ((count - 1) % selectedExperiment.config.num_doses) + 1;
    
    // Calculate prominence for faded strategy
    let prominence = currentProminence;
    if (selectedExperiment.config.notification_strategy === "faded") {
      prominence = Math.max(0.3, currentProminence - selectedExperiment.config.faded_opacity_decay);
      setCurrentProminence(prominence);
    }

    const notification = {
      id: `notif-${Date.now()}`,
      dose_number: doseNum,
      simulated_time: new Date().toISOString(),
      real_time: new Date().toISOString(),
      was_shown: true,
      notification_prominence: prominence,
      interval_from_last_minutes: currentInterval,
    };

    setCurrentNotification(notification);
    setNotificationShownAt(Date.now());
    setNotifications((prev) => [...prev, notification]);

    // Record notification to backend
    if (session) {
      api.recordNotification(session.id, notification);
    }
  };

  const handleOffloadingChoice = async (choice) => {
    if (!currentNotification || !session) return;
    
    const decisionTime = Date.now() - notificationShownAt;
    
    // Record the choice
    const event = {
      notification_id: currentNotification.id,
      dose_number: currentNotification.dose_number,
      choice: choice,
      decision_time_ms: decisionTime,
      notification_prominence: currentProminence,
      current_interval_minutes: currentInterval,
    };

    try {
      await api.recordOffloadingEvent(session.id, event);
    } catch (error) {
      console.error("Failed to record offloading event:", error);
    }

    // Update local results
    setResults(prev => ({
      ...prev,
      rememberChoices: prev.rememberChoices + (choice === "remember" ? 1 : 0),
      offloadChoices: prev.offloadChoices + (choice === "set_reminder" ? 1 : 0),
      decisionTimes: [...prev.decisionTimes, decisionTime]
    }));

    // For scaffolded strategy: increase interval after each "remember" choice
    if (selectedExperiment.config.notification_strategy === "scaffolded" && choice === "remember") {
      const newInterval = currentInterval * selectedExperiment.config.scaffolded_increase_factor;
      setCurrentInterval(Math.min(newInterval, 120)); // Cap at 120 minutes
    }

    // Dismiss notification
    setCurrentNotification(null);
    setNotificationShownAt(null);

    toast(choice === "remember" ? "You chose to remember" : "Reminder set", {
      icon: choice === "remember" ? "🧠" : "🔔",
    });
  };

  const triggerRecallProbe = useCallback(() => {
    if (!selectedExperiment) return;
    
    const probeTypes = ["dose_number", "doses_remaining"];
    const probeType = probeTypes[Math.floor(Math.random() * probeTypes.length)];
    const randomDose = Math.floor(Math.random() * selectedExperiment.config.num_doses) + 1;
    
    let question, correctAnswer;
    if (probeType === "dose_number") {
      question = "What was the dose number of your most recent reminder?";
      correctAnswer = String(notifications.length > 0 ? notifications[notifications.length - 1].dose_number : 1);
    } else {
      question = `How many doses are in this medication schedule?`;
      correctAnswer = String(selectedExperiment.config.num_doses);
    }

    const probe = {
      id: `probe-${Date.now()}`,
      probe_type: probeType,
      probe_time: new Date().toISOString(),
      probe_shown_timestamp: new Date().toISOString(),
      dose_asked: randomDose,
      correct_answer: correctAnswer,
      question: question,
    };

    setRecallProbe(probe);
    setProbeShownAt(Date.now());
  }, [selectedExperiment, notifications]);

  const submitProbeAnswer = async () => {
    if (!recallProbe || !session) return;
    
    const responseTime = Date.now() - probeShownAt;
    const isCorrect = probeAnswer.trim() === recallProbe.correct_answer;
    
    const completedProbe = {
      ...recallProbe,
      user_answer: probeAnswer,
      is_correct: isCorrect,
      response_time_ms: responseTime,
      response_submitted_timestamp: new Date().toISOString(),
    };

    try {
      await api.recordRecallProbe(session.id, completedProbe);
    } catch (error) {
      console.error("Failed to record probe:", error);
    }

    setResults(prev => ({
      ...prev,
      correct: prev.correct + (isCorrect ? 1 : 0),
      total: prev.total + 1,
      responseTimes: [...prev.responseTimes, responseTime]
    }));

    toast(isCorrect ? "Correct!" : `Incorrect. Answer was: ${recallProbe.correct_answer}`, {
      icon: isCorrect ? "✓" : "✗",
    });

    setRecallProbe(null);
    setProbeAnswer("");
    setProbeShownAt(null);

    // Trigger another probe if still in blackout
    if (phase === "blackout") {
      setTimeout(() => {
        if (phase === "blackout") triggerRecallProbe();
      }, 3000);
    }
  };

  const progressPercent = selectedExperiment
    ? (simulatedTime / selectedExperiment.config.total_duration_minutes) * 100
    : 0;
  const simulatedSeconds = Math.floor(simulatedTime * 60);
  const totalDurationSeconds = selectedExperiment
    ? selectedExperiment.config.total_duration_minutes * 60
    : 0;

  // Intro Phase
  if (phase === "intro") {
    return (
      <div className="participant-view min-h-screen">
        <header className="bg-white border-b">
          <div className="max-w-2xl mx-auto px-6 py-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">PM Research Lab</h1>
              <p className="text-xs text-gray-500">Simulation Instructions</p>
            </div>
          </div>
        </header>

        <main className="max-w-2xl mx-auto px-6 py-12">
          <Card className="p-8 animate-fadeIn">
            <h2 className="text-2xl font-semibold mb-6">Instructions</h2>
            
            <div className="space-y-6 text-gray-600">
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-medium text-blue-700">1</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Scenario</h3>
                  <p>Imagine you need to take a multi-dose medication. You'll receive reminder notifications.</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-medium text-green-700">2</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Your Choice (Important!)</h3>
                  <p>When each notification appears, you'll choose:</p>
                  <ul className="mt-2 space-y-1 text-sm">
                    <li className="flex items-center gap-2">
                      <Brain className="w-4 h-4 text-green-600" />
                      <strong>"I'll remember"</strong> - rely on your memory
                    </li>
                    <li className="flex items-center gap-2">
                      <Bell className="w-4 h-4 text-amber-600" />
                      <strong>"Set reminder"</strong> - offload to the system
                    </li>
                  </ul>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-medium text-amber-700">3</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Blackout Period</h3>
                  <p>Notifications will stop. You'll be tested on your memory of the dose information.</p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-medium text-violet-700">4</span>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Time Compression</h3>
                  <p>Time is accelerated—the simulation completes in a few minutes.</p>
                </div>
              </div>
            </div>

            {selectedExperiment && (
              <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <strong>Study:</strong> {selectedExperiment.name}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Strategy:</strong> {selectedExperiment.config.notification_strategy.replace(/_/g, " ")}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Doses:</strong> {selectedExperiment.config.num_doses}
                </p>
              </div>
            )}

            <div className="mt-8">
              <Button onClick={startSimulation} className="w-full" size="lg" data-testid="start-simulation-btn">
                <Play className="w-5 h-5 mr-2" />
                Begin Simulation
              </Button>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  // Running / Blackout Phase
  if (phase === "running" || phase === "blackout") {
    return (
      <div className={phase === "blackout" ? "blackout-mode" : "participant-view min-h-screen"}>
        <div className="max-w-2xl mx-auto px-6 py-8">
          {/* Status Header */}
          <div className="text-center mb-8">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
              phase === "blackout" ? "bg-amber-500/20 text-amber-300" : "bg-teal-100 text-teal-700"
            }`}>
              {phase === "blackout" ? (
                <>
                  <BellOff className="w-4 h-4" />
                  <span className="font-medium">Blackout Period - No Reminders</span>
                </>
              ) : (
                <>
                  <Bell className="w-4 h-4 animate-pulse-dot" />
                  <span className="font-medium">Simulation Active</span>
                </>
              )}
            </div>
          </div>

          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between text-sm mb-2">
              <span className={phase === "blackout" ? "text-gray-400" : "text-gray-500"}>Progress</span>
              <span className={`timer-display ${phase === "blackout" ? "text-white" : "text-gray-900"}`}>
                {simulatedSeconds} / {totalDurationSeconds} sec
              </span>
            </div>
            <div className={`progress-track h-2 ${phase === "blackout" ? "bg-gray-700" : ""}`}>
              <div className="progress-fill" style={{ width: `${Math.min(progressPercent, 100)}%` }} />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-3 mb-8">
            <Card className={`p-3 text-center ${phase === "blackout" ? "bg-gray-800 border-gray-700" : ""}`}>
              <p className={`text-xl font-bold timer-display ${phase === "blackout" ? "text-white" : ""}`}>
                {notifications.length}
              </p>
              <p className={`text-xs ${phase === "blackout" ? "text-gray-400" : "text-gray-500"}`}>Notifications</p>
            </Card>
            <Card className={`p-3 text-center ${phase === "blackout" ? "bg-gray-800 border-gray-700" : ""}`}>
              <p className={`text-xl font-bold timer-display text-green-600`}>
                {results.rememberChoices}
              </p>
              <p className={`text-xs ${phase === "blackout" ? "text-gray-400" : "text-gray-500"}`}>Remembered</p>
            </Card>
            <Card className={`p-3 text-center ${phase === "blackout" ? "bg-gray-800 border-gray-700" : ""}`}>
              <p className={`text-xl font-bold timer-display text-amber-600`}>
                {results.offloadChoices}
              </p>
              <p className={`text-xs ${phase === "blackout" ? "text-gray-400" : "text-gray-500"}`}>Offloaded</p>
            </Card>
            <Card className={`p-3 text-center ${phase === "blackout" ? "bg-gray-800 border-gray-700" : ""}`}>
              <p className={`text-xl font-bold timer-display ${phase === "blackout" ? "text-white" : ""}`}>
                {results.total > 0 ? Math.round((results.correct / results.total) * 100) : 0}%
              </p>
              <p className={`text-xs ${phase === "blackout" ? "text-gray-400" : "text-gray-500"}`}>Accuracy</p>
            </Card>
          </div>

          {/* Current Notification with Offloading Choice */}
          {currentNotification && (
            <div 
              className="notification-card p-6 mb-6 animate-slideInRight"
              style={{ opacity: currentProminence }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <Bell className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Medication Reminder</p>
                  <p className="text-gray-600">Time for Dose {currentNotification.dose_number}</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-500 mb-4">
                Will you remember this dose information, or would you like to set a reminder?
              </p>

              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant="success"
                  onClick={() => handleOffloadingChoice("remember")}
                  className="flex items-center justify-center gap-2"
                  data-testid="remember-btn"
                >
                  <Brain className="w-4 h-4" />
                  I'll Remember
                </Button>
                <Button
                  variant="warning"
                  onClick={() => handleOffloadingChoice("set_reminder")}
                  className="flex items-center justify-center gap-2"
                  data-testid="offload-btn"
                >
                  <Bookmark className="w-4 h-4" />
                  Set Reminder
                </Button>
              </div>
            </div>
          )}

          {/* Recall Probe */}
          {recallProbe && (
            <Card className={`p-6 animate-fadeIn ${phase === "blackout" ? "bg-gray-800 border-gray-700" : ""}`}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                  <HelpCircle className="w-5 h-5 text-violet-600" />
                </div>
                <h3 className={`font-semibold ${phase === "blackout" ? "text-white" : ""}`}>
                  Memory Test
                </h3>
              </div>
              <p className={`mb-4 ${phase === "blackout" ? "text-gray-300" : "text-gray-600"}`}>
                {recallProbe.question}
              </p>
              <div className="flex gap-3">
                <Input
                  type="text"
                  value={probeAnswer}
                  onChange={(e) => setProbeAnswer(e.target.value)}
                  placeholder="Your answer..."
                  className="flex-1"
                  data-testid="probe-input"
                  onKeyPress={(e) => e.key === "Enter" && submitProbeAnswer()}
                />
                <Button onClick={submitProbeAnswer} data-testid="submit-probe-btn">
                  Submit
                </Button>
              </div>
              <p className={`text-xs mt-2 ${phase === "blackout" ? "text-gray-500" : "text-gray-400"}`}>
                <Timer className="w-3 h-3 inline mr-1" />
                Response time is being recorded
              </p>
            </Card>
          )}

          {/* Waiting message */}
          {!recallProbe && !currentNotification && (
            <div className="text-center py-12">
              <div className={`inline-block p-4 rounded-full ${phase === "blackout" ? "bg-gray-800" : "bg-gray-100"} mb-4`}>
                <Clock className={`w-8 h-8 ${phase === "blackout" ? "text-gray-400" : "text-gray-400"}`} />
              </div>
              <p className={phase === "blackout" ? "text-gray-400" : "text-gray-500"}>
                {phase === "blackout" ? "Waiting for next memory test..." : "Simulation in progress..."}
              </p>
              {selectedExperiment?.config.notification_strategy === "scaffolded" && phase === "running" && (
                <p className="text-xs text-gray-400 mt-2">
                  Current interval: {Math.round(currentInterval)} minutes
                </p>
              )}
              {selectedExperiment?.config.notification_strategy === "faded" && phase === "running" && (
                <p className="text-xs text-gray-400 mt-2">
                  Notification visibility: {Math.round(currentProminence * 100)}%
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Complete Phase
  return (
    <div className="participant-view min-h-screen flex items-center justify-center p-4">
      <Card className="p-8 max-w-lg w-full text-center animate-fadeIn">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-semibold mb-2">Simulation Complete</h2>
        <p className="text-gray-600 mb-8">Thank you for participating in this research study.</p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{results.total}</p>
            <p className="text-sm text-gray-500">Memory Tests</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <p className="text-2xl font-bold text-green-700">
              {results.total > 0 ? Math.round((results.correct / results.total) * 100) : 0}%
            </p>
            <p className="text-sm text-green-700">Recall Accuracy</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-xl font-bold text-blue-700">{results.rememberChoices}</p>
            <p className="text-sm text-blue-700">Times "Remembered"</p>
          </div>
          <div className="p-4 bg-amber-50 rounded-lg">
            <p className="text-xl font-bold text-amber-700">{results.offloadChoices}</p>
            <p className="text-sm text-amber-700">Times "Offloaded"</p>
          </div>
        </div>

        {results.decisionTimes.length > 0 && (
          <div className="p-4 bg-violet-50 rounded-lg mb-6">
            <p className="text-lg font-bold text-violet-700">
              {Math.round(results.decisionTimes.reduce((a, b) => a + b, 0) / results.decisionTimes.length)}ms
            </p>
            <p className="text-sm text-violet-700">Avg. Decision Time</p>
          </div>
        )}

        <p className="text-sm text-gray-500 mb-6">
          Your responses have been recorded anonymously for research purposes.
        </p>

        <Button onClick={() => navigate("/")} variant="secondary" className="w-full">
          Return to Home
        </Button>
      </Card>
    </div>
  );
};

// ========================
// RESEARCHER INTERFACE
// ========================

const ResearcherLogin = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (isAuthenticated) navigate("/researcher/dashboard");
  }, [isAuthenticated, navigate]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (login(password)) {
      navigate("/researcher/dashboard");
    } else {
      setError("Invalid password");
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-10"
      style={{
        background:
          "radial-gradient(circle at top, rgba(30, 58, 95, 0.08), transparent 32%), linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%)",
      }}
    >
      <Card className="w-full max-w-lg overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/95 shadow-[0_30px_90px_rgba(15,23,42,0.08)] animate-fadeIn">
        <div className="border-b border-slate-100 bg-[linear-gradient(135deg,#1E3A5F_0%,#29486F_100%)] px-8 py-8 text-white">
          <div className="mb-6 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/12 ring-1 ring-white/15 backdrop-blur">
              <Brain className="h-7 w-7 text-white" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-200">Secure Portal</p>
              <p className="text-sm text-slate-200/90">Researcher dashboard access</p>
            </div>
          </div>
          <h1 className="text-4xl font-semibold text-white">Researcher Access</h1>
          <p className="mt-3 max-w-md text-base text-slate-200/90">
            Sign in to manage experiments, review participation data, and export research results.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-8 py-8">
          <div className="mb-6 rounded-2xl border border-slate-200 bg-slate-50/80 p-5">
            <p className="text-sm font-medium text-slate-800">PM Research Lab Dashboard</p>
            <p className="mt-1 text-sm text-slate-500">
              Use the researcher password to enter the protected admin area.
            </p>
          </div>

          <div className="mb-4">
            <label className="mb-2 block text-sm font-semibold uppercase tracking-[0.16em] text-slate-600">Password</label>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              className="input h-14 rounded-xl border-slate-200 bg-white text-base text-slate-900 placeholder:text-slate-400 focus:border-[#1E3A5F] focus:shadow-[0_0_0_4px_rgba(30,58,95,0.12)]"
              placeholder="Enter researcher password"
              data-testid="password-input"
            />
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </div>

          <Button
            type="submit"
            className="mt-6 h-14 w-full rounded-xl bg-[#1E3A5F] text-base font-semibold text-white shadow-[0_18px_30px_rgba(30,58,95,0.18)] hover:bg-[#29486F]"
            data-testid="login-btn"
          >
            Access Dashboard
          </Button>
        </form>

        <div className="border-t border-slate-100 px-8 py-5 text-center">
          <Link to="/" className="text-sm font-medium text-slate-500 transition-colors hover:text-slate-800">
            ← Back to participant view
          </Link>
        </div>
      </Card>
    </div>
  );
};

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/researcher/login" replace />;
  return children;
};

const ResearcherLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const navItems = [
    { path: "/researcher/dashboard", icon: BarChart3, label: "Dashboard" },
    { path: "/researcher/experiments", icon: Beaker, label: "Experiments" },
    { path: "/researcher/analytics", icon: TrendingUp, label: "Analytics" },
    { path: "/researcher/progress", icon: ListTodo, label: "Progress" },
    { path: "/researcher/reports", icon: FileText, label: "Reports" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {sidebarOpen && <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />}

      <aside className={`fixed top-0 left-0 h-screen w-60 bg-white border-r z-50 transform transition-transform lg:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-5 border-b">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#1E3A5F] flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900 text-sm">PM Research Lab</h1>
              <p className="text-xs text-gray-500">Researcher Portal</p>
            </div>
          </div>
        </div>

        <nav className="p-3">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors ${
                  isActive ? "bg-[#1E3A5F] text-white" : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-3 border-t">
          <button
            onClick={() => { logout(); navigate("/"); }}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-100 w-full"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="lg:ml-60">
        <header className="h-14 border-b bg-white sticky top-0 z-30 flex items-center px-4 lg:px-6">
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-2 hover:bg-gray-100 rounded mr-3">
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex-1" />
          <span className="text-sm text-gray-500">
            {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
          </span>
        </header>
        <main className="p-4 lg:p-6 max-w-6xl mx-auto">{children}</main>
      </div>
    </div>
  );
};

const ResearcherDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [overviewRes, comparisonRes] = await Promise.all([
        api.getOverviewAnalytics(),
        api.getOffloadingComparison()
      ]);
      setAnalytics(overviewRes.data);
      setComparison(comparisonRes.data);
    } catch (error) {
      console.error("Failed to load:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedData = async () => {
    try {
      await api.seedData();
      toast.success("Sample data loaded");
      loadData();
    } catch (error) {
      toast.error("Failed to load sample data");
    }
  };

  const handleExportAll = async () => {
    try {
      const response = await api.exportFullData();
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `full_research_data_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      toast.success("Full data exported");
    } catch (error) {
      toast.error("Export failed");
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  const stats = [
    { label: "Experiments", value: analytics?.total_experiments || 0, icon: Beaker },
    { label: "Participants", value: analytics?.total_participants || 0, icon: Users },
    { label: "Completed", value: analytics?.completed_sessions || 0, icon: CheckCircle2 },
    { label: "Remember", value: analytics?.total_remember_choices || 0, icon: Brain, color: "text-green-600" },
    { label: "Offload", value: analytics?.total_offload_choices || 0, icon: Bookmark, color: "text-amber-600" },
  ];

  return (
    <div className="space-y-6" data-testid="researcher-dashboard">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm">Research overview and cognitive offloading analysis</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={handleSeedData}>
            <RotateCcw className="w-4 h-4 mr-1" />
            Load Sample
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExportAll}>
            <Download className="w-4 h-4 mr-1" />
            Export All
          </Button>
          <Button size="sm" onClick={() => navigate("/researcher/experiments")}>
            <Plus className="w-4 h-4 mr-1" />
            New Experiment
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stats.map((stat, idx) => (
          <Card key={stat.label} className={`p-4 animate-fadeIn stagger-${idx + 1}`}>
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center ${stat.color || ""}`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Offloading Comparison */}
      {comparison?.comparison?.length > 0 && (
        <Card className="p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Offloading Rate by Strategy (Key Thesis Data)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={comparison.comparison}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="strategy" stroke="#6B7280" fontSize={12} />
              <YAxis stroke="#6B7280" fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="offloading_rate" fill="#F59E0B" name="Offloading %" radius={[4, 4, 0, 0]} />
              <Bar dataKey="avg_recall_accuracy" fill="#10B981" name="Recall Accuracy %" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-2">
            {[
              { label: "View Experiments", path: "/researcher/experiments", icon: Beaker },
              { label: "Analytics & Export", path: "/researcher/analytics", icon: Download },
              { label: "Track Progress", path: "/researcher/progress", icon: ListTodo },
            ].map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <item.icon className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-700">{item.label}</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500" />
              </Link>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Strategy Distribution</h3>
          {Object.entries(analytics?.strategy_breakdown || {}).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(analytics.strategy_breakdown).map(([strategy, count]) => (
                <div key={strategy} className="flex items-center justify-between">
                  <StrategyBadge strategy={strategy} />
                  <span className="text-sm font-medium text-gray-900">{count} experiments</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No experiments yet</p>
          )}
        </Card>
      </div>
    </div>
  );
};

// Simplified versions of other researcher pages (keeping core functionality)
const ResearcherExperiments = () => {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [qrExperiment, setQrExperiment] = useState(null);
  const [formData, setFormData] = useState({
    name: "", description: "", notification_strategy: "just_in_time",
    notification_frequency_minutes: 30, blackout_duration_minutes: 60,
    total_duration_minutes: 180, time_compression_factor: 60, num_doses: 3,
    scaffolded_increase_factor: 1.5, faded_opacity_decay: 0.15,
  });

  useEffect(() => { loadExperiments(); }, []);

  const loadExperiments = async () => {
    try {
      const response = await api.getExperiments();
      setExperiments(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createExperiment({
        name: formData.name,
        description: formData.description,
        config: {
          notification_strategy: formData.notification_strategy,
          notification_frequency_minutes: parseInt(formData.notification_frequency_minutes),
          blackout_duration_minutes: parseInt(formData.blackout_duration_minutes),
          total_duration_minutes: parseInt(formData.total_duration_minutes),
          time_compression_factor: parseFloat(formData.time_compression_factor),
          num_doses: parseInt(formData.num_doses),
          scaffolded_increase_factor: parseFloat(formData.scaffolded_increase_factor),
          faded_opacity_decay: parseFloat(formData.faded_opacity_decay),
        },
      });
      toast.success("Experiment created");
      setShowModal(false);
      loadExperiments();
    } catch (error) {
      toast.error("Failed to create experiment");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this experiment?")) return;
    try {
      await api.deleteExperiment(id);
      toast.success("Deleted");
      loadExperiments();
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Experiments</h1>
          <p className="text-gray-500 text-sm">Configure notification strategy experiments</p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="w-4 h-4 mr-1" /> New Experiment
        </Button>
      </div>

      {experiments.length === 0 ? (
        <EmptyState icon={Beaker} title="No experiments" description="Create your first experiment" 
          action={<Button onClick={() => setShowModal(true)}>Create Experiment</Button>} />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {experiments.map((exp) => (
            <Card key={exp.id} className="p-5" hover>
              <div className="flex items-start justify-between mb-3">
                <StrategyBadge strategy={exp.config.notification_strategy} />
                <button onClick={() => handleDelete(exp.id)} className="p-1 hover:bg-red-50 rounded text-gray-400 hover:text-red-600">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <h3 className="font-medium text-gray-900 mb-1">{exp.name}</h3>
              {exp.description && <p className="text-sm text-gray-500 mb-3 line-clamp-2">{exp.description}</p>}
              
              {/* Shareable Link */}
              <div className="mb-3 p-2.5 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-500 flex items-center gap-1">
                    <Share2 className="w-3 h-3" /> Share Code
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setQrExperiment(exp)}
                      className="text-xs text-[#0D9488] hover:text-[#047857] flex items-center gap-1 font-medium"
                      data-testid={`qr-btn-${exp.id}`}
                    >
                      QR
                    </button>
                    <button
                      onClick={() => {
                        const link = `${window.location.origin}/study/${exp.share_code || 'N/A'}`;
                        navigator.clipboard.writeText(link);
                        toast.success("Study link copied!");
                      }}
                      className="text-xs text-[#1E3A5F] hover:text-[#2D5A8A] flex items-center gap-1 font-medium"
                      data-testid={`copy-link-${exp.id}`}
                    >
                      <Copy className="w-3 h-3" /> Copy Link
                    </button>
                  </div>
                </div>
                <code className="text-sm font-mono text-[#1E3A5F] font-bold" data-testid={`share-code-${exp.id}`}>
                  {exp.share_code || 'N/A'}
                </code>
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Sessions</span><span>{exp.completed_sessions}/{exp.total_sessions}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Doses</span><span>{exp.config.num_doses}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Duration</span><span>{exp.config.total_duration_minutes}m</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Speed</span><span className="mono">{exp.config.time_compression_factor}x</span></div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Create Experiment" size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
          <Textarea label="Description" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
          <Select label="Notification Strategy" value={formData.notification_strategy} onChange={(e) => setFormData({ ...formData, notification_strategy: e.target.value })}
            options={[
              { value: "just_in_time", label: "Just-in-Time (Constant intervals)" },
              { value: "scaffolded", label: "Scaffolded (Increasing intervals)" },
              { value: "faded", label: "Faded (Decreasing prominence)" },
              { value: "control", label: "Control (No reminders)" },
            ]} />
          <div className="grid grid-cols-3 gap-4">
            <Input label="Frequency (min)" type="number" min="0" value={formData.notification_frequency_minutes} onChange={(e) => setFormData({ ...formData, notification_frequency_minutes: e.target.value })} />
            <Input label="Blackout (min)" type="number" min="5" value={formData.blackout_duration_minutes} onChange={(e) => setFormData({ ...formData, blackout_duration_minutes: e.target.value })} />
            <Input label="Duration (min)" type="number" min="30" value={formData.total_duration_minutes} onChange={(e) => setFormData({ ...formData, total_duration_minutes: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <Input label="Doses" type="number" min="1" max="10" value={formData.num_doses} onChange={(e) => setFormData({ ...formData, num_doses: e.target.value })} />
            <Input label="Speed (x)" type="number" min="1" value={formData.time_compression_factor} onChange={(e) => setFormData({ ...formData, time_compression_factor: e.target.value })} />
            {formData.notification_strategy === "scaffolded" && (
              <Input label="Interval Increase" type="number" min="1" step="0.1" value={formData.scaffolded_increase_factor} onChange={(e) => setFormData({ ...formData, scaffolded_increase_factor: e.target.value })} />
            )}
            {formData.notification_strategy === "faded" && (
              <Input label="Opacity Decay" type="number" min="0.05" max="0.5" step="0.05" value={formData.faded_opacity_decay} onChange={(e) => setFormData({ ...formData, faded_opacity_decay: e.target.value })} />
            )}
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)} className="flex-1">Cancel</Button>
            <Button type="submit" className="flex-1">Create</Button>
          </div>
        </form>
      </Modal>

      {/* QR Code Modal */}
      <Modal isOpen={!!qrExperiment} onClose={() => setQrExperiment(null)} title="Study QR Code" size="sm">
        {qrExperiment && (
          <div className="flex flex-col items-center">
            <div className="p-6 bg-white rounded-xl border border-gray-100 mb-4" data-testid="qr-code-container">
              <QRCodeSVG
                value={`${window.location.origin}/study/${qrExperiment.share_code}`}
                size={200}
                bgColor="#ffffff"
                fgColor="#1E3A5F"
                level="H"
                includeMargin={false}
              />
            </div>
            <h3 className="font-semibold text-gray-900 text-center mb-1">{qrExperiment.name}</h3>
            <p className="text-sm text-gray-500 mb-1">
              Strategy: {qrExperiment.config.notification_strategy.replace(/_/g, " ")}
            </p>
            <code className="text-sm font-mono text-[#1E3A5F] font-bold bg-gray-50 px-3 py-1 rounded mb-4">
              {qrExperiment.share_code}
            </code>
            <p className="text-xs text-gray-400 text-center mb-4 max-w-xs">
              Participants can scan this QR code to join this study directly.
            </p>
            <div className="flex gap-2 w-full">
              <Button
                variant="secondary"
                size="sm"
                className="flex-1"
                onClick={() => {
                  const link = `${window.location.origin}/study/${qrExperiment.share_code}`;
                  navigator.clipboard.writeText(link);
                  toast.success("Link copied!");
                }}
                data-testid="qr-copy-link-btn"
              >
                <Copy className="w-4 h-4 mr-1" /> Copy Link
              </Button>
              <Button
                variant="primary"
                size="sm"
                className="flex-1"
                onClick={() => {
                  const svg = document.querySelector('[data-testid="qr-code-container"] svg');
                  if (!svg) return;
                  const svgData = new XMLSerializer().serializeToString(svg);
                  const canvas = document.createElement('canvas');
                  canvas.width = 400; canvas.height = 400;
                  const ctx = canvas.getContext('2d');
                  ctx.fillStyle = '#ffffff';
                  ctx.fillRect(0, 0, 400, 400);
                  const img = new Image();
                  img.onload = () => {
                    ctx.drawImage(img, 0, 0, 400, 400);
                    const a = document.createElement('a');
                    a.download = `qr_${qrExperiment.share_code}.png`;
                    a.href = canvas.toDataURL('image/png');
                    a.click();
                    toast.success("QR code downloaded!");
                  };
                  img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
                }}
                data-testid="qr-download-btn"
              >
                <Download className="w-4 h-4 mr-1" /> Download QR
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

const ResearcherAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [overview, comp] = await Promise.all([api.getOverviewAnalytics(), api.getOffloadingComparison()]);
        setAnalytics(overview.data);
        setComparison(comp.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleExport = async (type) => {
    try {
      if (type === "pdf") {
        const response = await axios.get(`${API}/export/pdf-report`, { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        const a = document.createElement("a");
        a.href = url;
        a.download = `pm_research_report_${new Date().toISOString().split('T')[0]}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success("PDF report downloaded");
        return;
      }
      
      let response;
      if (type === "full") {
        response = await api.exportFullData();
      } else if (type === "validated") {
        response = await api.exportValidatedData();
      } else {
        response = await api.exportSessions(null, "csv");
      }
      const blob = (type === "full" || type === "validated")
        ? new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" })
        : new Blob([response.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = type === "full" ? "full_research_data.json" : type === "validated" ? "validated_research_data.json" : "sessions.csv";
      a.click();
      toast.success("Export downloaded");
    } catch (error) {
      toast.error("Export failed");
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Analytics</h1>
          <p className="text-gray-500 text-sm">Offloading behavior analysis and data export</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleExport("csv")} data-testid="export-csv-btn">
            <Download className="w-4 h-4 mr-1" /> Sessions CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport("full")} data-testid="export-json-btn">
            <Download className="w-4 h-4 mr-1" /> Full JSON
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport("validated")} data-testid="export-validated-btn">
            <Shield className="w-4 h-4 mr-1" /> Validated Data
          </Button>
          <Button variant="primary" size="sm" onClick={() => handleExport("pdf")} data-testid="export-pdf-btn">
            <FileDown className="w-4 h-4 mr-1" /> PDF Report
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Experiments", value: analytics?.total_experiments },
          { label: "Participants", value: analytics?.total_participants },
          { label: "Remember Choices", value: analytics?.total_remember_choices, color: "text-green-600" },
          { label: "Offload Choices", value: analytics?.total_offload_choices, color: "text-amber-600" },
        ].map((s) => (
          <Card key={s.label} className="p-4 text-center">
            <p className={`text-xl font-bold ${s.color || "text-gray-900"}`}>{s.value || 0}</p>
            <p className="text-xs text-gray-500">{s.label}</p>
          </Card>
        ))}
      </div>

      {comparison?.comparison?.length > 0 && (
        <Card className="p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Strategy Comparison (Thesis Data)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3">Strategy</th>
                  <th className="text-right py-2 px-3">Sessions</th>
                  <th className="text-right py-2 px-3">Offload Rate</th>
                  <th className="text-right py-2 px-3">Remember Rate</th>
                  <th className="text-right py-2 px-3">Recall Accuracy</th>
                  <th className="text-right py-2 px-3">Avg Decision Time</th>
                </tr>
              </thead>
              <tbody>
                {comparison.comparison.map((row) => (
                  <tr key={row.experiment_id} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3"><StrategyBadge strategy={row.strategy} /></td>
                    <td className="text-right py-2 px-3">{row.num_sessions}</td>
                    <td className="text-right py-2 px-3 text-amber-600 font-medium">{row.offloading_rate}%</td>
                    <td className="text-right py-2 px-3 text-green-600 font-medium">{row.remember_rate}%</td>
                    <td className="text-right py-2 px-3">{row.avg_recall_accuracy}%</td>
                    <td className="text-right py-2 px-3 mono">{row.avg_decision_time_ms}ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

const ResearcherProgress = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ title: "", description: "", week_number: 1, priority: "p1", target_date: "", notes: "", category: "" });

  useEffect(() => { loadTasks(); }, []);

  const loadTasks = async () => {
    try {
      const response = await api.getTasks();
      setTasks(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createTask(formData);
      toast.success("Task created");
      setShowModal(false);
      setFormData({ title: "", description: "", week_number: 1, priority: "p1", target_date: "", notes: "", category: "" });
      loadTasks();
    } catch (error) {
      toast.error("Failed");
    }
  };

  const handleStatusToggle = async (task) => {
    try {
      await api.updateTask(task.id, { status: task.status === "completed" ? "not_started" : "completed" });
      loadTasks();
    } catch (error) {
      toast.error("Failed");
    }
  };

  const tasksByWeek = tasks.reduce((acc, task) => {
    const week = task.week_number;
    if (!acc[week]) acc[week] = [];
    acc[week].push(task);
    return acc;
  }, {});

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Progress Tracker</h1>
          <p className="text-gray-500 text-sm">Weekly tasks and milestones</p>
        </div>
        <Button onClick={() => setShowModal(true)}><Plus className="w-4 h-4 mr-1" /> New Task</Button>
      </div>

      {Object.keys(tasksByWeek).length === 0 ? (
        <EmptyState icon={ListTodo} title="No tasks" description="Create tasks to track progress" action={<Button onClick={() => setShowModal(true)}>Create Task</Button>} />
      ) : (
        <div className="space-y-4">
          {Object.keys(tasksByWeek).sort((a, b) => a - b).map((week) => (
            <Card key={week} className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-900">Week {week}</h3>
                <span className="text-sm text-gray-500">{tasksByWeek[week].filter(t => t.status === "completed").length}/{tasksByWeek[week].length}</span>
              </div>
              <div className="space-y-2">
                {tasksByWeek[week].map((task) => (
                  <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <button onClick={() => handleStatusToggle(task)} className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${task.status === "completed" ? "bg-green-500 border-green-500" : "border-gray-300"}`}>
                        {task.status === "completed" && <CheckCircle2 className="w-3 h-3 text-white" />}
                      </button>
                      <span className={`text-sm ${task.status === "completed" ? "text-gray-400 line-through" : ""}`}>{task.title}</span>
                      <PriorityBadge priority={task.priority} />
                      {task.category && <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">{task.category}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="New Task">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Title" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required />
          <div className="grid grid-cols-3 gap-4">
            <Input label="Week" type="number" min="1" max="52" value={formData.week_number} onChange={(e) => setFormData({ ...formData, week_number: parseInt(e.target.value) })} />
            <Select label="Priority" value={formData.priority} onChange={(e) => setFormData({ ...formData, priority: e.target.value })} options={[{ value: "p0", label: "P0" }, { value: "p1", label: "P1" }, { value: "p2", label: "P2" }, { value: "p3", label: "P3" }]} />
            <Input label="Category" value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })} placeholder="e.g., Dev" />
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)} className="flex-1">Cancel</Button>
            <Button type="submit" className="flex-1">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

const ResearcherReports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ week_number: 1, start_date: "", end_date: "", summary: "", accomplishments: "", challenges: "", next_week_goals: "" });

  useEffect(() => { loadReports(); }, []);

  const loadReports = async () => {
    try {
      const response = await api.getWeeklyReports();
      setReports(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.createWeeklyReport({
        ...formData,
        week_number: parseInt(formData.week_number),
        accomplishments: formData.accomplishments.split("\n").filter(Boolean),
        challenges: formData.challenges.split("\n").filter(Boolean),
        next_week_goals: formData.next_week_goals.split("\n").filter(Boolean),
      });
      toast.success("Report created");
      setShowModal(false);
      loadReports();
    } catch (error) {
      toast.error("Failed");
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Weekly Reports</h1>
          <p className="text-gray-500 text-sm">Document progress and milestones</p>
        </div>
        <Button onClick={() => setShowModal(true)}><Plus className="w-4 h-4 mr-1" /> New Report</Button>
      </div>

      {reports.length === 0 ? (
        <EmptyState icon={FileText} title="No reports" description="Create weekly reports" action={<Button onClick={() => setShowModal(true)}>Create Report</Button>} />
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.id} className="p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900">Week {report.week_number}</h3>
                  <p className="text-sm text-gray-500">{new Date(report.start_date).toLocaleDateString()} - {new Date(report.end_date).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-[#1E3A5F]">{report.tasks_completed}/{report.tasks_total}</p>
                  <p className="text-xs text-gray-500">tasks</p>
                </div>
              </div>
              {report.summary && <p className="text-gray-600 mb-4">{report.summary}</p>}
              <div className="grid md:grid-cols-3 gap-4 text-sm">
                <div>
                  <h4 className="font-medium text-green-700 mb-1">Accomplishments</h4>
                  <ul className="space-y-1">{report.accomplishments.map((item, i) => <li key={i} className="text-gray-600">• {item}</li>)}</ul>
                </div>
                <div>
                  <h4 className="font-medium text-amber-700 mb-1">Challenges</h4>
                  <ul className="space-y-1">{report.challenges.map((item, i) => <li key={i} className="text-gray-600">• {item}</li>)}</ul>
                </div>
                <div>
                  <h4 className="font-medium text-blue-700 mb-1">Next Week</h4>
                  <ul className="space-y-1">{report.next_week_goals.map((item, i) => <li key={i} className="text-gray-600">• {item}</li>)}</ul>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="New Weekly Report" size="lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Input label="Week #" type="number" min="1" max="52" value={formData.week_number} onChange={(e) => setFormData({ ...formData, week_number: e.target.value })} required />
            <Input label="Start Date" type="date" value={formData.start_date} onChange={(e) => setFormData({ ...formData, start_date: e.target.value })} required />
            <Input label="End Date" type="date" value={formData.end_date} onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} required />
          </div>
          <Textarea label="Summary" value={formData.summary} onChange={(e) => setFormData({ ...formData, summary: e.target.value })} />
          <Textarea label="Accomplishments (one per line)" value={formData.accomplishments} onChange={(e) => setFormData({ ...formData, accomplishments: e.target.value })} />
          <Textarea label="Challenges (one per line)" value={formData.challenges} onChange={(e) => setFormData({ ...formData, challenges: e.target.value })} />
          <Textarea label="Next Week Goals (one per line)" value={formData.next_week_goals} onChange={(e) => setFormData({ ...formData, next_week_goals: e.target.value })} />
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)} className="flex-1">Cancel</Button>
            <Button type="submit" className="flex-1">Create Report</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// ========================
// Main App
// ========================

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-center" />
        <Routes>
          <Route path="/" element={<ParticipantLanding />} />
          <Route path="/study/:shareCode" element={<StudyJoinRedirect />} />
          <Route path="/participate/consent" element={<ParticipantConsent />} />
          <Route path="/participate/demographics" element={<ParticipantDemographics />} />
          <Route path="/participate/simulation" element={<ParticipantSimulation />} />
          <Route path="/researcher/login" element={<ResearcherLogin />} />
          <Route path="/researcher/dashboard" element={<ProtectedRoute><ResearcherLayout><ResearcherDashboard /></ResearcherLayout></ProtectedRoute>} />
          <Route path="/researcher/experiments" element={<ProtectedRoute><ResearcherLayout><ResearcherExperiments /></ResearcherLayout></ProtectedRoute>} />
          <Route path="/researcher/analytics" element={<ProtectedRoute><ResearcherLayout><ResearcherAnalytics /></ResearcherLayout></ProtectedRoute>} />
          <Route path="/researcher/progress" element={<ProtectedRoute><ResearcherLayout><ResearcherProgress /></ResearcherLayout></ProtectedRoute>} />
          <Route path="/researcher/reports" element={<ProtectedRoute><ResearcherLayout><ResearcherReports /></ResearcherLayout></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
