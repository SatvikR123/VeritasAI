import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  History, 
  Sparkles, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  Plus, 
  Menu, 
  ChevronRight, 
  FileText,
  Clock,
  Compass,
  Settings,
  User,
  Bell,
  Activity,
  ShieldCheck,
  BarChart3,
  Globe2,
  Moon,
  Sun,
  ArrowUpRight,
  TrendingUp,
  Cpu,
  RefreshCw,
  Eye,
  X,
  BookOpenCheck,
  Newspaper,
  Layers,
  Workflow,
  Download
} from 'lucide-react';
import { marked } from 'marked';
import { motion, AnimatePresence } from 'framer-motion';

const PIPELINE_STEPS = [
  { id: 'collect', label: 'News Collection Agent', desc: 'Queries DDG/Yahoo for raw news and triggers local scraper nodes' },
  { id: 'cluster', label: 'Event Clustering Agent', desc: 'Clusters incoming articles into event streams using keyword graph grouping' },
  { id: 'summarize', label: 'Summarization Agent', desc: 'Extracts critical developments, overall briefing, and chronology timelines' },
  { id: 'verify', label: 'Fact Verification Agent', desc: 'Validates factual assertions and flags contradictions across media portals' },
  { id: 'detect_bias', label: 'Bias Detection Agent', desc: 'Analyzes political framing, emotional tone, and media spin' },
  { id: 'assess_credibility', label: 'Credibility Assessment Agent', desc: 'Scores publisher trust levels and consistency benchmarks' },
  { id: 'consensus', label: 'Consensus Verdict Agent', desc: 'Integrates reports, resolves conflicting claims, and drafts final consensus' },
  { id: 'reporter', label: 'Report Compilation Agent', desc: 'Assembles full briefing and structural intelligence report markup' }
];

const MOCK_TRENDING = [
  { topic: "Red Sea Shipping Security", volume: "1.4K articles", sentiment: "Volatile", country: "YE", color: "text-red-400" },
  { topic: "AI Act Compliance Directive", volume: "920 articles", sentiment: "Neutral", country: "EU", color: "text-yellow-400" },
  { topic: "Semiconductor Fab Expansion", volume: "2.5K articles", sentiment: "Bullish", country: "TW", color: "text-emerald-400" },
  { topic: "Global Trade Tariff Policies", volume: "1.8K articles", sentiment: "Unstable", country: "US", color: "text-red-400" }
];

const MOCK_ANALYTICS = [
  { label: "Total Articles Analyzed", value: "24", icon: Newspaper, desc: "Real-time source documents" },
  { label: "Verified News Outlets", value: "88%", icon: ShieldCheck, desc: "Out of total indexed domain list" },
  { label: "Avg Credibility Score", value: "91.2%", icon: Activity, desc: "Cross-verified source accuracy" },
  { label: "Active Agent Nodes", value: "8/8 Online", icon: Cpu, desc: "Distributed processing units" }
];

export default function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [history, setHistory] = useState([]);
  const [activeStep, setActiveStep] = useState(null);
  const [stepLogs, setStepLogs] = useState({});
  const [pacingLog, setPacingLog] = useState('');
  const [currentReport, setCurrentReport] = useState(null);
  const [notificationsCount, setNotificationsCount] = useState(2);

  // Authentication State
  const [user, setUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authTab, setAuthTab] = useState('login');
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [authRole, setAuthRole] = useState('Security Analyst');
  const [authError, setAuthError] = useState('');
  const [googleClientId, setGoogleClientId] = useState(null);

  // Live analytics and trending topics
  const [trendingTopics, setTrendingTopics] = useState([]);
  const [systemAnalytics, setSystemAnalytics] = useState(null);

  // On component mount
  useEffect(() => {
    // 1. Fetch Google Client ID from backend config
    const getConfig = async () => {
      try {
        const res = await fetch('/api/config');
        const data = await res.json();
        if (data.google_client_id) {
          setGoogleClientId(data.google_client_id);
          
          // Load Google Identity Services SDK script dynamically
          const script = document.createElement("script");
          script.src = "https://accounts.google.com/gsi/client";
          script.async = true;
          script.defer = true;
          document.body.appendChild(script);
        }
      } catch (err) {
        console.error("Failed to load backend config:", err);
      }
    };
    getConfig();

    // 2. Verify local token and load user
    checkUserSession();

    // 3. Fetch initial analytics and trending topics
    fetchAnalytics();
    fetchTrending();
  }, []);

  // Sync history when user changes
  useEffect(() => {
    fetchHistory();
  }, [user]);

  // Dynamically initialize the Google Identity Services button once modal opens
  useEffect(() => {
    if (authModalOpen && googleClientId && window.google) {
      try {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleLoginSuccess
        });
        window.google.accounts.id.renderButton(
          document.getElementById("google-signin-button"),
          { theme: "dark", size: "large", width: "100%", text: "continue_with" }
        );
      } catch (err) {
        console.error("Failed to initialize Google button:", err);
      }
    }
  }, [authModalOpen, googleClientId]);

  const checkUserSession = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        localStorage.removeItem('token');
        setUser(null);
      }
    } catch (err) {
      console.error("Session verification failed:", err);
      localStorage.removeItem('token');
      setUser(null);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics');
      if (res.ok) {
        const data = await res.json();
        setSystemAnalytics(data);
      }
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
    }
  };

  const fetchTrending = async () => {
    try {
      const res = await fetch('/api/trending');
      if (res.ok) {
        const data = await res.json();
        setTrendingTopics(data);
      }
    } catch (err) {
      console.error("Failed to fetch trending:", err);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const res = await fetch('/api/history', { headers });
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error("Failed to load history:", e);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: authUsername, password: authPassword })
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setAuthModalOpen(false);
        setAuthUsername('');
        setAuthPassword('');
        fetchAnalytics();
      } else {
        const err = await res.json();
        setAuthError(err.detail || "Invalid credentials.");
      }
    } catch (err) {
      setAuthError("Login failed. Check server connection.");
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: authUsername,
          password: authPassword,
          full_name: authFullName,
          role: ""
        })
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setAuthModalOpen(false);
        setAuthUsername('');
        setAuthPassword('');
        setAuthFullName('');
        fetchAnalytics();
      } else {
        const err = await res.json();
        setAuthError(err.detail || "Registration failed.");
      }
    } catch (err) {
      setAuthError("Registration failed. Check server connection.");
    }
  };

  const handleGoogleLoginSuccess = async (response) => {
    try {
      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: response.credential })
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.token);
        setUser(data.user);
        setAuthModalOpen(false);
        fetchAnalytics();
      } else {
        const err = await res.json();
        setAuthError(err.detail || "Google Login failed.");
      }
    } catch (err) {
      setAuthError("Google Login connection failed.");
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (err) {
        console.error("Logout request failed:", err);
      }
    }
    localStorage.removeItem('token');
    setUser(null);
    setCurrentReport(null);
    fetchAnalytics();
  };

  const handleStartAnalysis = (searchQuery) => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setCurrentReport(null);
    setPacingLog('');
    
    // Initialize step states
    const initialLogs = {};
    PIPELINE_STEPS.forEach(s => {
      initialLogs[s.id] = { status: 'idle', log: '' };
    });
    setStepLogs(initialLogs);
    setActiveStep('collect');
    setStepLogs(prev => ({ ...prev, collect: { status: 'running', log: 'Starting web search news gathering...' } }));

    // Start Server-Sent Events stream
    const token = localStorage.getItem('token');
    let url = `/api/analyze?query=${encodeURIComponent(searchQuery)}`;
    if (token) {
      url += `&token=${token}`;
    }
    const eventSource = new EventSource(url);

    eventSource.addEventListener('status', (e) => {
      try {
        const data = JSON.parse(e.data);
        const { node, status, message } = data;
        
        if (node) {
          setActiveStep(node);
          setStepLogs(prev => {
            const updated = { ...prev };
            // Mark previous steps as completed
            const nodeIndex = PIPELINE_STEPS.findIndex(s => s.id === node);
            PIPELINE_STEPS.forEach((s, idx) => {
              if (idx < nodeIndex) {
                updated[s.id].status = 'completed';
              }
            });
            updated[node] = { status, log: message };
            return updated;
          });
        } else if (message) {
          setPacingLog(message);
        }
      } catch (err) {
        console.error("Failed to parse status event", err);
      }
    });

    eventSource.addEventListener('result', (e) => {
      try {
        const data = JSON.parse(e.data);
        setCurrentReport(data.report);
        setLoading(false);
        eventSource.close();
        fetchHistory(); // Refresh history
        fetchAnalytics(); // Refresh analytics
        fetchTrending(); // Refresh trending topics
      } catch (err) {
        console.error("Failed to parse result event", err);
        setLoading(false);
        eventSource.close();
      }
    });

    eventSource.addEventListener('error', (e) => {
      console.error("SSE stream error", e);
      setPacingLog("System pacing: Retrying request or sleeping to avoid rate limit locks...");
      if (eventSource.readyState === EventSource.CLOSED) {
        setLoading(false);
      }
    });
  };

  const handleDownloadPDF = () => {
    if (!currentReport) return;
    
    const iframe = document.createElement('iframe');
    iframe.style.position = 'fixed';
    iframe.style.right = '0';
    iframe.style.bottom = '0';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = '0';
    document.body.appendChild(iframe);

    const doc = iframe.contentWindow.document;
    const reportHtml = marked(currentReport.report_markdown || '');
    
    // Copy all style and link tags from main document to iframe
    const styles = Array.from(document.querySelectorAll('style, link[rel="stylesheet"]'))
      .map(el => el.outerHTML)
      .join('\n');
      
    doc.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${currentReport.query} - News Intelligence Dossier</title>
          ${styles}
        </head>
        <body class="markdown-body" style="background: white !important; color: #1E293B !important; padding: 40px !important;">
          ${reportHtml}
          <script>
            window.onload = () => {
              setTimeout(() => {
                window.focus();
                window.print();
                setTimeout(() => {
                  window.frameElement.remove();
                }, 500);
              }, 500);
            };
          </script>
        </body>
      </html>
    `);
    doc.close();
  };

  const handleDeleteHistory = async (id, e) => {
    e.stopPropagation();
    try {
      const token = localStorage.getItem('token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      await fetch(`/api/history/${id}`, { method: 'DELETE', headers });
      fetchHistory();
      if (currentReport && currentReport.id === id) {
        setCurrentReport(null);
      }
    } catch (err) {
      console.error("Failed to delete history item", err);
    }
  };

  const handleSelectHistory = async (item) => {
    setCurrentReport(item);
    setLoading(false);
  };

  const resetWorkspace = () => {
    setCurrentReport(null);
    setLoading(false);
    setQuery('');
  };

  const displayAnalytics = [
    { label: "Total Articles Analyzed", value: systemAnalytics?.total_articles || "24", icon: Newspaper, desc: "Real-time source documents" },
    { label: "Verified News Outlets", value: systemAnalytics?.verified_outlets || "88%", icon: ShieldCheck, desc: "Out of total indexed domain list" },
    { label: "Avg Credibility Score", value: systemAnalytics?.avg_credibility || "91.2%", icon: Activity, desc: "Cross-verified source accuracy" },
    { label: "Active Agent Nodes", value: systemAnalytics?.active_nodes || "8/8 Online", icon: Cpu, desc: "Distributed processing units" }
  ];

  const displayTrending = trendingTopics.length > 0 ? trendingTopics : MOCK_TRENDING;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F17] text-[#F8FAFC] antialiased">
      
      {/* Sidebar Panel */}
      <aside 
        className={`flex flex-col border-r border-[rgba(255,255,255,0.06)] bg-[#0E131F] h-full transition-all duration-300 ease-in-out shrink-0 z-20 ${
          sidebarOpen ? 'w-80' : 'w-0 overflow-hidden border-r-transparent'
        }`}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between px-6 border-b border-[rgba(255,255,255,0.06)] h-16 shrink-0">
          <div className="flex items-center gap-3 cursor-pointer" onClick={resetWorkspace}>
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-accent-blue to-accent-purple shadow-[0_0_15px_rgba(79,126,255,0.3)]">
              <Sparkles className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="font-semibold text-base tracking-wide bg-gradient-to-r from-[#8AB4F8] to-[#C58AF9] bg-clip-text text-transparent">
              VERITAS AI
            </span>
          </div>
          
          <button 
            onClick={resetWorkspace}
            className="flex items-center justify-center p-2 rounded-lg bg-[#141B2D] border border-[rgba(255,255,255,0.06)] hover:bg-[#1E2943] text-accent-blue transition-all"
            title="New Analysis"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          <div className="flex items-center gap-2 px-2 text-2xs font-semibold tracking-wider text-[#64748B] uppercase">
            <History className="w-3.5 h-3.5" />
            <span>Recent Analyses</span>
          </div>

          {history.length === 0 ? (
            <div className="text-center text-xs text-[#64748B] py-8 border border-dashed border-[rgba(255,255,255,0.04)] rounded-xl px-4">
              No recent searches index
            </div>
          ) : (
            <div className="space-y-1">
              {history.map((item) => {
                const isActive = currentReport && currentReport.id === item.id;
                return (
                  <div 
                    key={item.id}
                    onClick={() => handleSelectHistory(item)}
                    className={`group flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer border transition-all duration-200 ${
                      isActive 
                        ? 'bg-[#182238] border-[rgba(79,126,255,0.2)] text-[#F8FAFC]' 
                        : 'bg-transparent border-transparent text-[#94A3B8] hover:bg-[#121B2B] hover:text-[#F8FAFC]'
                    }`}
                  >
                    <div className="flex flex-col gap-1 min-w-0 flex-1">
                      <span className="text-xs font-medium truncate pr-2">{item.query}</span>
                      <span className="text-4xs text-[#64748B] flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5" />
                        {new Date(item.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <button 
                      onClick={(e) => handleDeleteHistory(item.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 rounded bg-transparent hover:bg-[#FF5C7A]/10 text-[#64748B] hover:text-danger transition-all duration-200"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sidebar Footer User Profile */}
        <div className="p-4 border-t border-[rgba(255,255,255,0.06)] bg-[#0A0D15]">
          {user ? (
            <div className="flex items-center gap-3">
              <div className="relative w-9 h-9 rounded-full bg-[#18233C] flex items-center justify-center border border-[rgba(255,255,255,0.08)] overflow-hidden">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.full_name} className="w-full h-full object-cover" />
                ) : (
                  <User className="w-4 h-4 text-[#8AB4F8]" />
                )}
                <div className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-success rounded-full border-2 border-[#0B0F17]"></div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-[#F8FAFC] truncate">{user.full_name}</p>
              </div>
              <button 
                onClick={handleLogout}
                className="p-2 rounded-lg text-[#64748B] hover:text-[#FF5C7A] hover:bg-[#FF5C7A]/10 transition-all"
                title="Log Out"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button 
              onClick={() => { setAuthError(''); setAuthTab('login'); setAuthModalOpen(true); }}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#141B2D] border border-[rgba(255,255,255,0.06)] hover:bg-[#1E2943] text-[#8AB4F8] hover:text-white transition-all text-xs font-semibold"
            >
              <User className="w-4 h-4" />
              <span>Sign In to Veritas</span>
            </button>
          )}
        </div>
      </aside>

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col h-full bg-[#0B0F17] relative overflow-hidden z-10">
        
        {/* Top Header navbar */}
        <header className="flex items-center justify-between px-8 border-b border-[rgba(255,255,255,0.06)] h-16 shrink-0 bg-[#0C101A]/80 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg bg-[#141B2D] border border-[rgba(255,255,255,0.06)] text-[#94A3B8] hover:text-[#F8FAFC] transition-all"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
              <span className="text-[#F8FAFC] font-semibold">
                {currentReport ? 'Intelligence Report' : loading ? 'Agent Session' : 'Search Console'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
          </div>
        </header>

        {/* Workspace Body */}
        <div className="flex-1 overflow-y-auto px-8 py-8 flex flex-col">
          
          {/* Welcome Screen / Idle State */}
          {!loading && !currentReport && (
            <motion.div 
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="max-w-6xl mx-auto w-full flex flex-col space-y-12"
            >
              {/* Hero Section */}
              <div className="text-center max-w-2xl mx-auto">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[rgba(124,92,255,0.1)] border border-[rgba(124,92,255,0.2)] text-[10px] font-semibold text-accent-purple tracking-wider uppercase mb-6">
                  <Cpu className="w-3.5 h-3.5 animate-pulse" />
                  <span>Agentic Consensus Mesh</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
                  Veritas AI
                </h1>
                <p className="text-sm text-[#94A3B8] leading-relaxed">
                  Aggregate, verify, cluster and analyze global events using cooperative AI agents. Enter your search query below to compile a fresh intelligence report.
                </p>
              </div>

              {/* Search Box */}
              <div className="max-w-3xl w-full mx-auto relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-accent-blue to-accent-purple rounded-2xl blur-lg opacity-25 group-focus-within:opacity-45 transition duration-1000"></div>
                <div className="relative flex items-center bg-[#111827] border border-[rgba(255,255,255,0.06)] rounded-2xl p-3 shadow-2xl focus-within:border-[rgba(79,126,255,0.4)] transition-all">
                  <Search className="w-5.5 h-5.5 text-[#64748B] ml-3 shrink-0" />
                  <input 
                    type="text" 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleStartAnalysis(query)}
                    placeholder="Search geopolitical events, companies, elections, conflicts..." 
                    className="flex-1 bg-transparent border-0 outline-none px-4 py-3 text-sm text-[#F8FAFC] placeholder-[#64748B]"
                  />
                  <div className="flex items-center gap-3 shrink-0 mr-1">
                    <button 
                      onClick={() => handleStartAnalysis(query)}
                      disabled={!query.trim()}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent-blue text-xs font-semibold text-white hover:bg-accent-blue/90 disabled:bg-[#161F30] disabled:text-[#64748B] transition-all"
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>Analyze</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick suggested pill cards */}
              <div className="max-w-3xl w-full mx-auto">
                <div className="flex items-center gap-2 text-2xs font-semibold text-[#64748B] uppercase tracking-wider mb-3">
                  <TrendingUp className="w-3.5 h-3.5" />
                  <span>Suggested intelligence investigations</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { title: "FIFA Ticket Prices", query: "FIFA world cup ticket pricing", desc: "Analysis of ticket markup trends" },
                    { title: "Iran Conflict Impacts", query: "Iran Israel security escalation geopolitical impact", desc: "Geopolitical risk analysis" },
                    { title: "SpaceX Launch Security", query: "SpaceX Starship orbital test restrictions", desc: "Safety & airspace compliance" },
                    { title: "Election Integrity Risks", query: "Election cybersecurity interference reports", desc: "Digital systems safety" },
                    { title: "Core Inflation Targets", query: "Federal Reserve core inflation hikes consensus", desc: "Macroeconomic briefing" },
                    { title: "Market Volatility", query: "NASDAQ technology index correction factors", desc: "Financial sector report" }
                  ].map((s, idx) => (
                    <div 
                      key={idx}
                      onClick={() => { setQuery(s.query); handleStartAnalysis(s.query); }}
                      className="group flex flex-col p-4 rounded-xl bg-[#111827]/60 border border-[rgba(255,255,255,0.05)] cursor-pointer hover:bg-[#141D30] hover:border-[rgba(79,126,255,0.2)] transition-all duration-300 shadow-md hover:-translate-y-0.5"
                    >
                      <span className="text-xs font-bold text-white group-hover:text-accent-blue transition-colors">{s.title}</span>
                      <span className="text-[10px] text-[#64748B] mt-1 line-clamp-1">{s.desc}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Divider */}
              <div className="border-t border-[rgba(255,255,255,0.06)] w-full my-6"></div>

              {/* Grid with statistics and recent items below fold */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Left side: Recent Intelligence (Timeline) */}
                <div className="lg:col-span-7 space-y-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <FileText className="w-4.5 h-4.5 text-accent-blue" />
                      <span>Recent Intel Reports</span>
                    </h3>
                  </div>

                  <div className="space-y-4">
                    {history.slice(0, 3).map((item) => (
                      <div 
                        key={item.id}
                        onClick={() => handleSelectHistory(item)}
                        className="p-5 rounded-xl bg-[#111827]/45 border border-[rgba(255,255,255,0.05)] hover:border-[rgba(79,126,255,0.2)] hover:bg-[#111827] cursor-pointer transition-all duration-300 flex items-start gap-4 shadow-lg group"
                      >
                        <div className="p-2.5 rounded-lg bg-[#18233C] text-accent-blue group-hover:text-white group-hover:bg-accent-blue transition-all">
                          <BookOpenCheck className="w-4.5 h-4.5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-5xs font-medium text-[#64748B]">{new Date(item.timestamp).toLocaleString()}</span>
                          </div>
                          <h4 className="text-xs font-bold text-[#F8FAFC] truncate mb-2 group-hover:text-accent-blue transition-colors">
                            {item.query}
                          </h4>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[9px] font-medium bg-[#162725] text-success border border-success/15">
                              Credibility: {item.credibility_score ? `${(item.credibility_score * 100).toFixed(0)}%` : '92%'}
                            </span>
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[9px] font-medium bg-[#1F2937] text-[#94A3B8]">
                              Sources: 3 verified
                            </span>
                          </div>
                        </div>
                        <ArrowUpRight className="w-4.5 h-4.5 text-[#64748B] opacity-0 group-hover:opacity-100 group-hover:text-accent-blue transition-all shrink-0" />
                      </div>
                    ))}
                    
                    {history.length === 0 && (
                      <div className="text-center py-10 rounded-xl border border-dashed border-[rgba(255,255,255,0.04)] bg-[#111827]/10">
                        <p className="text-xs text-[#64748B]">No geopolitical analysis report index compiled yet.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right side: Analytics & Swarm & Trending */}
                <div className="lg:col-span-5 space-y-6">
                  
                  {/* Swarm KPIs */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <BarChart3 className="w-4.5 h-4.5 text-accent-purple" />
                      <span>System Analytics</span>
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      {displayAnalytics.map((stat, idx) => (
                        <div key={idx} className="p-4 rounded-xl bg-[#111827]/45 border border-[rgba(255,255,255,0.05)] shadow-md">
                          <div className="flex items-center gap-2 text-[10px] font-semibold text-[#64748B] uppercase tracking-wider mb-2">
                            <stat.icon className="w-4 h-4 text-accent-blue" />
                            <span>{stat.label}</span>
                          </div>
                          <p className="text-lg font-bold text-[#F8FAFC]">{stat.value}</p>
                          <p className="text-[9px] text-[#64748B] mt-0.5">{stat.desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Trending Geopolitical volume */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Globe2 className="w-4.5 h-4.5 text-accent-blue" />
                      <span>Trending Security Topics</span>
                    </h3>
                    <div className="rounded-xl bg-[#111827]/30 border border-[rgba(255,255,255,0.05)] p-4 space-y-3">
                      {displayTrending.map((item, idx) => (
                        <div 
                          key={idx} 
                          onClick={() => { setQuery(item.topic); handleStartAnalysis(item.topic); }}
                          className="flex items-center justify-between border-b border-[rgba(255,255,255,0.04)] pb-2.5 last:border-0 last:pb-0 cursor-pointer hover:bg-[rgba(255,255,255,0.02)] p-1 rounded transition-all"
                        >
                          <div className="min-w-0">
                            <p className="text-xs font-semibold text-[#F8FAFC] truncate">{item.topic}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] text-[#64748B]">{item.volume}</span>
                              <span className="w-1 h-1 bg-[#64748B] rounded-full"></span>
                              <span className={`text-[10px] font-medium ${item.color}`}>{item.sentiment}</span>
                            </div>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-[#1E293B] border border-[rgba(255,255,255,0.06)] text-[9px] text-[#94A3B8] font-bold">
                            {item.country}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>

              </div>
            </motion.div>
          )}

          {/* Stepper / Loading State */}
          {loading && !currentReport && (
            <div className="max-w-4xl mx-auto w-full flex flex-col space-y-8 py-6">
              
              {/* Spinning / Pacing Section */}
              <div className="flex flex-col items-center text-center space-y-3 pb-4">
                <div className="relative w-16 h-16 rounded-full border border-[rgba(255,255,255,0.06)] bg-[#111827] flex items-center justify-center shadow-[0_0_30px_rgba(79,126,255,0.1)]">
                  <div className="absolute inset-0.5 rounded-full border border-t-accent-blue border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
                  <Cpu className="w-6 h-6 text-accent-blue animate-pulse" />
                </div>
                <h3 className="text-base font-bold text-[#F8FAFC] tracking-wide">
                  Activating Agent Consensus Swarm
                </h3>
                <p className="text-xs text-[#94A3B8] max-w-md leading-relaxed">
                  Executing multi-agent LangGraph workflow sequentially. Evaluating contradictions, extracting chronological events, and verifying claim entities.
                </p>
              </div>

              {/* Status logs block */}
              {pacingLog && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="mx-auto w-full max-w-xl px-4 py-3 rounded-lg bg-[rgba(124,92,255,0.05)] border border-[rgba(124,92,255,0.15)] text-[11px] font-mono text-[#C58AF9] text-center"
                >
                  <span className="inline-block w-2 h-2 rounded-full bg-accent-purple animate-ping mr-2.5"></span>
                  {pacingLog}
                </motion.div>
              )}

              {/* Pipeline Nodes List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto w-full">
                {PIPELINE_STEPS.map((step) => {
                  const stepState = stepLogs[step.id] || { status: 'idle', log: '' };
                  const isActive = activeStep === step.id;
                  const isCompleted = stepState.status === 'completed';
                  const isRunning = stepState.status === 'running';

                  return (
                    <motion.div 
                      key={step.id} 
                      layout
                      className={`p-4 rounded-xl border flex gap-4 transition-all duration-300 ${
                        isActive 
                          ? 'bg-[#151C2C] border-accent-blue shadow-[0_0_20px_rgba(79,126,255,0.1)]' 
                          : isCompleted 
                            ? 'bg-[#111827]/40 border-[rgba(255,255,255,0.05)] opacity-80' 
                            : 'bg-[#111827]/25 border-[rgba(255,255,255,0.03)] opacity-40'
                      }`}
                    >
                      <div className="mt-0.5 shrink-0">
                        {isCompleted ? (
                          <div className="w-5 h-5 rounded-full bg-[#162725] border border-success/20 flex items-center justify-center text-success">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          </div>
                        ) : isRunning ? (
                          <div className="w-5 h-5 rounded-full bg-[#152033] border border-accent-blue/35 flex items-center justify-center">
                            <Loader2 className="w-3.5 h-3.5 text-accent-blue animate-spin" />
                          </div>
                        ) : (
                          <div className="w-5 h-5 rounded-full bg-[#1c2331] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#64748B]">
                            <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-bold ${isActive ? 'text-accent-blue' : 'text-[#F8FAFC]'}`}>
                            {step.label}
                          </span>
                          <span className="text-[9px] font-bold tracking-wider uppercase text-[#64748B]">
                            {stepState.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#64748B] leading-snug">{step.desc}</p>
                        {stepState.log && (
                          <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-[10px] font-mono text-[#8AB4F8] mt-2 pt-1.5 border-t border-[rgba(255,255,255,0.04)] break-words"
                          >
                            {stepState.log}
                          </motion.div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>

            </div>
          )}

          {/* Compiled Markdown Report View */}
          {!loading && currentReport && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.99 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="max-w-4xl mx-auto w-full flex flex-col space-y-6"
            >
              
              {/* Report Header stats */}
              <div className="p-6 rounded-xl bg-[#0E1325] border border-[rgba(79,126,255,0.12)] shadow-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
                <div className="flex-1 min-w-0">
                  <span className="text-[10px] font-bold text-accent-blue uppercase tracking-wider block mb-1">
                    Compiled Intelligence Briefing
                  </span>
                  <h2 className="text-xl font-bold text-white leading-snug truncate pr-4">
                    {currentReport.query}
                  </h2>
                  <span className="text-[10px] text-[#64748B] flex items-center gap-1.5 mt-2">
                    <Clock className="w-3.5 h-3.5 text-[#64748B]" />
                    Generated: {new Date(currentReport.timestamp).toLocaleString()}
                  </span>
                </div>
                
                <div className="flex items-center gap-4 shrink-0">
                  <div className="flex items-center gap-3 bg-[#111827]/40 px-4 py-2 rounded-xl border border-[rgba(255,255,255,0.06)]">
                    <div className="flex flex-col">
                      <span className="text-[8px] font-bold text-[#64748B] uppercase tracking-wider">Credibility</span>
                      <span className="text-sm font-extrabold text-success mt-0.5">
                        {currentReport.credibility_score ? `${(currentReport.credibility_score * 100).toFixed(0)}%` : '92%'}
                      </span>
                    </div>
                    <div className="w-8 h-8 rounded-full bg-[#162725] border border-success/20 flex items-center justify-center text-success">
                      <ShieldCheck className="w-4.5 h-4.5" />
                    </div>
                  </div>

                  <button 
                    onClick={handleDownloadPDF}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#141B2D] border border-[rgba(255,255,255,0.06)] hover:bg-[#1E2943] text-accent-blue hover:text-white transition-all text-xs font-semibold shadow-md active:scale-95 cursor-pointer"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download PDF</span>
                  </button>
                  
                  <button 
                    onClick={resetWorkspace}
                    className="px-5 py-2.5 rounded-lg bg-accent-blue text-xs font-semibold text-white hover:bg-accent-blue/90 shadow-md active:scale-95 transition-all cursor-pointer"
                  >
                    Done
                  </button>
                </div>
              </div>

              {/* Rendered HTML Container */}
              <div className="p-8 rounded-xl bg-[#111827]/70 border border-[rgba(255,255,255,0.06)] shadow-xl">
                <div 
                  className="markdown-body"
                  dangerouslySetInnerHTML={{ __html: marked(currentReport.report_markdown || '') }} 
                />
              </div>

            </motion.div>
          )}

        </div>
      </main>

      {/* Authentication Modal */}
      <AnimatePresence>
        {authModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-sm overflow-hidden rounded-2xl bg-[#0E131F] border border-[rgba(255,255,255,0.08)] shadow-[0_20px_50px_rgba(0,0,0,0.5)] p-6 flex flex-col space-y-5"
            >
              {/* Close Button */}
              <button 
                onClick={() => setAuthModalOpen(false)}
                className="absolute top-4 right-4 p-1.5 rounded-lg text-[#64748B] hover:text-[#F8FAFC] hover:bg-[#141B2D] transition-all"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Title */}
              <div className="text-center space-y-1">
                <h3 className="text-lg font-bold tracking-tight text-white">
                  {authTab === 'login' ? 'Access Veritas AI' : 'Create Security Account'}
                </h3>
                <p className="text-[11px] text-[#64748B] leading-snug">
                  {authTab === 'login' 
                    ? 'Log in to sync your search history and access platform metrics.' 
                    : 'Register your secure credentials to join the analysis swarm.'}
                </p>
              </div>

              {/* Tabs */}
              <div className="grid grid-cols-2 p-1 bg-[#090D16] rounded-lg border border-[rgba(255,255,255,0.04)]">
                <button 
                  onClick={() => { setAuthTab('login'); setAuthError(''); }}
                  className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                    authTab === 'login' ? 'bg-[#182238] text-white' : 'text-[#64748B] hover:text-[#94A3B8]'
                  }`}
                >
                  Log In
                </button>
                <button 
                  onClick={() => { setAuthTab('register'); setAuthError(''); }}
                  className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                    authTab === 'register' ? 'bg-[#182238] text-white' : 'text-[#64748B] hover:text-[#94A3B8]'
                  }`}
                >
                  Register
                </button>
              </div>

              {authError && (
                <div className="p-2 text-[10px] bg-red-500/10 border border-red-500/20 text-[#FF5C7A] rounded-lg text-center font-medium">
                  {authError}
                </div>
              )}

              {/* Forms */}
              <form onSubmit={authTab === 'login' ? handleLogin : handleRegister} className="space-y-3.5">
                {authTab === 'register' && (
                  <>
                    <div className="space-y-1">
                      <label className="text-[9px] font-bold text-[#64748B] uppercase tracking-wider">Full Name</label>
                      <input 
                        type="text" 
                        required
                        value={authFullName}
                        onChange={(e) => setAuthFullName(e.target.value)}
                        placeholder="Sarah Jenkins"
                        className="w-full px-3 py-1.5 text-xs bg-[#090D16] border border-[rgba(255,255,255,0.06)] rounded-lg outline-none focus:border-accent-blue/50 text-white"
                      />
                    </div>
                    

                  </>
                )}

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-[#64748B] uppercase tracking-wider">Username / Email</label>
                  <input 
                    type="text" 
                    required
                    value={authUsername}
                    onChange={(e) => setAuthUsername(e.target.value)}
                    placeholder="sarah.j"
                    className="w-full px-3 py-1.5 text-xs bg-[#090D16] border border-[rgba(255,255,255,0.06)] rounded-lg outline-none focus:border-accent-blue/50 text-white"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-[#64748B] uppercase tracking-wider">Password</label>
                  <input 
                    type="password" 
                    required
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-1.5 text-xs bg-[#090D16] border border-[rgba(255,255,255,0.06)] rounded-lg outline-none focus:border-accent-blue/50 text-white"
                  />
                </div>

                <button 
                  type="submit"
                  className="w-full py-2 bg-gradient-to-r from-accent-blue to-accent-purple text-xs font-semibold text-white rounded-lg hover:brightness-110 active:scale-[0.98] transition-all shadow-md mt-2"
                >
                  {authTab === 'login' ? 'Confirm Login' : 'Create Secure Profile'}
                </button>
              </form>

              {/* Google OAuth Button Section */}
              {googleClientId && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="w-full border-b border-[rgba(255,255,255,0.04)]"></span>
                    <span className="px-3 text-[10px] text-[#64748B] whitespace-nowrap">OR</span>
                    <span className="w-full border-b border-[rgba(255,255,255,0.04)]"></span>
                  </div>
                  
                  {/* Google Login Button container */}
                  <div className="flex justify-center w-full">
                    <div id="google-signin-button" className="w-full"></div>
                  </div>
                </div>
              )}

            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
