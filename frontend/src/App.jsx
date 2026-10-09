import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import DashboardOverview from './components/DashboardOverview';
import IncidentMap from './components/IncidentMap';
import IncidentDetailView from './components/IncidentDetailView';
import HumanApprovalQueue from './components/HumanApprovalQueue';
import AgentChatConsole from './components/AgentChatConsole';
import IncidentReportModal from './components/IncidentReportModal';
import { api } from './services/api';
import {
  Layers,
  Map,
  ShieldCheck,
  Bot,
  Filter,
  Search,
  Droplets,
  AlertTriangle,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function App() {
  const [stats, setStats] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'map', 'approval', 'agent'
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Agent Chat State
  const [chatLog, setChatLog] = useState([
    {
      role: 'assistant',
      content:
        '👋 Welcome to **Monsoon Sentinel**.\n\nI am the autonomous emergency dispatcher orchestrating municipal waterlogging response using the **Strands Agents SDK** and a local **Amazon SageMaker AI mock adapter**.\n\nSelect any incident to inspect its deterministic risk factors, request operational response equipment, or verify post-clearance culvert telemetry.',
      thought_process: [
        'Local Strands Agents SDK initialized with 12 explicit tools.',
        'Deterministic Python Risk Engine active for telemetry evaluation.',
        'SQLite repository ready for incident persistence.'
      ]
    }
  ]);
  const [loadingChat, setLoadingChat] = useState(false);

  const fetchData = async () => {
    setIsRefreshing(true);
    try {
      const [statsData, incidentsData] = await Promise.all([
        api.getStats(),
        api.getIncidents(),
      ]);
      setStats(statsData);
      setIncidents(incidentsData);

      if (incidentsData.length > 0) {
        // If current selection is still valid, keep it; otherwise default to first
        setSelectedIncident((prev) => {
          if (!prev) return incidentsData[0];
          const matched = incidentsData.find((i) => i.id === prev.id);
          return matched || incidentsData[0];
        });
      }
    } catch (err) {
      console.error('Failed to load dashboard state:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Workflow Handlers
  const handleAnalyze = async (incidentId) => {
    setLoadingAction(true);
    try {
      const updated = await api.analyzeIncident(incidentId);
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error analyzing risk: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handlePrioritize = async (incidentId) => {
    setLoadingAction(true);
    try {
      const updated = await api.prioritizeIncident(incidentId);
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error prioritizing incident: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleRecommend = async (incidentId) => {
    setLoadingAction(true);
    try {
      const updated = await api.recommendResponse(incidentId);
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error recommending response: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleTriage = async (incidentId) => {
    setLoadingAction(true);
    try {
      const result = await api.triageIncident(incidentId);
      // Fetch latest state
      const updated = await api.getIncident(incidentId);
      setSelectedIncident(updated);
      await fetchData();

      // Add to chat log
      setChatLog((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.agent_explanation || `Completed automated triage for ${incidentId}.`,
          thought_process: [
            `Evaluated risk score: ${result.risk_score} (${result.severity})`,
            'Executed 5 sequential Strands Agent tools.',
            'Plan submitted for human supervisor sign-off.'
          ],
          tool_traces: result.tool_traces
        }
      ]);
    } catch (err) {
      alert(`Error running agent triage: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleRequestApproval = async (incidentId) => {
    setLoadingAction(true);
    try {
      const updated = await api.recommendResponse(incidentId);
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error submitting for approval: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleHumanReview = async (incidentId, approved, reviewer, rationale) => {
    setLoadingAction(true);
    try {
      const updated = await api.submitApproval(incidentId, { approved, reviewer, rationale });
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error reviewing approval: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleResolve = async (incidentId, resolution_notes, evidence_url) => {
    setLoadingAction(true);
    try {
      const updated = await api.resolveIncident(incidentId, { resolution_notes, evidence_url });
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error resolving incident: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleVerify = async (incidentId, sensor_flow_rate_lps, post_clearance_depth_cm, simulate_failure) => {
    setLoadingAction(true);
    try {
      const updated = await api.verifyIncident(incidentId, {
        sensor_flow_rate_lps,
        post_clearance_depth_cm,
        simulate_failure,
      });
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error verifying incident: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCitizenSubmit = async (formData) => {
    const created = await api.submitReport(formData);
    await fetchData();
    setSelectedIncident(created);
  };

  const handleSendMessage = async (msgText) => {
    setChatLog((prev) => [...prev, { role: 'user', content: msgText }]);
    setLoadingChat(true);

    try {
      const res = await api.chatAgent({
        message: msgText,
        incident_id: selectedIncident ? selectedIncident.id : null,
      });

      setChatLog((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.response,
          thought_process: res.thought_process,
          tool_traces: res.tool_traces,
        },
      ]);
      await fetchData();
    } catch (err) {
      setChatLog((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error executing agent tool: ${err.message}`,
        },
      ]);
    } finally {
      setLoadingChat(false);
    }
  };

  // Filtered incidents list
  const filteredIncidents = incidents.filter((i) => {
    const matchesFilter =
      statusFilter === 'ALL' ||
      (statusFilter === 'ACTIVE' && !['RESOLVED', 'VERIFIED', 'REJECTED', 'CANCELLED'].includes(i.status)) ||
      (statusFilter === 'AWAITING_APPROVAL' && i.status === 'AWAITING_APPROVAL') ||
      (statusFilter === 'CRITICAL' && (i.risk_assessment?.severity === 'CRITICAL' || i.risk_assessment?.severity === 'HIGH'));

    const matchesSearch =
      i.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      i.report.ward_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      i.report.description.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const pendingApprovalIncidents = incidents.filter((i) => i.status === 'AWAITING_APPROVAL');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header
        onOpenReportModal={() => setIsReportModalOpen(true)}
        onRefresh={fetchData}
        isRefreshing={isRefreshing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Dynamic Statistics Bar */}
        <DashboardOverview stats={stats} />

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'dashboard'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Operational Triage</span>
          </button>

          <button
            onClick={() => setActiveTab('map')}
            className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'map'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Map className="w-4 h-4" />
            <span>Ward GIS Map</span>
          </button>

          <button
            onClick={() => setActiveTab('approval')}
            className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition relative cursor-pointer ${
              activeTab === 'approval'
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Supervisor Queue</span>
            {pendingApprovalIncidents.length > 0 && (
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping ml-1" />
            )}
          </button>

          <button
            onClick={() => setActiveTab('agent')}
            className={`px-3 py-1.5 rounded-lg font-medium flex items-center gap-1.5 transition cursor-pointer ${
              activeTab === 'agent'
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>Strands Agent Console</span>
          </button>
        </div>

        {/* View Layouts */}
        {activeTab === 'map' ? (
          <div className="space-y-4">
            <IncidentMap
              incidents={incidents}
              selectedIncident={selectedIncident}
              onSelectIncident={(inc) => {
                setSelectedIncident(inc);
                setActiveTab('dashboard');
              }}
            />
          </div>
        ) : activeTab === 'approval' ? (
          <HumanApprovalQueue
            pendingIncidents={pendingApprovalIncidents}
            onReview={handleHumanReview}
            loadingAction={loadingAction}
          />
        ) : activeTab === 'agent' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AgentChatConsole
                selectedIncident={selectedIncident}
                onSendMessage={handleSendMessage}
                chatLog={chatLog}
                loadingChat={loadingChat}
              />
            </div>
            <div>
              <IncidentDetailView
                incident={selectedIncident}
                onAnalyze={handleAnalyze}
                onPrioritize={handlePrioritize}
                onRecommend={handleRecommend}
                onTriage={handleTriage}
                onRequestApproval={handleRequestApproval}
                onResolve={handleResolve}
                onVerify={handleVerify}
                loadingAction={loadingAction}
              />
            </div>
          </div>
        ) : (
          /* Dashboard Triage Tab (Split View) */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Incidents Filterable List (4 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Droplets className="w-4 h-4 text-blue-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Reported Incidents ({filteredIncidents.length})
                    </h3>
                  </div>
                  <span className="text-[11px] text-slate-400">Click to inspect</span>
                </div>

                {/* Search Bar */}
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by Ward, ID, landmark..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-blue-500"
                  />
                </div>

                {/* Filter Pills */}
                <div className="flex items-center gap-1.5 flex-wrap text-[11px]">
                  {['ALL', 'ACTIVE', 'AWAITING_APPROVAL', 'CRITICAL'].map((f) => (
                    <button
                      key={f}
                      onClick={() => setStatusFilter(f)}
                      className={`px-2.5 py-1 rounded-md font-medium transition cursor-pointer ${
                        statusFilter === f
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {f.replace('_', ' ')}
                    </button>
                  ))}
                </div>

                {/* Incidents Scrollable List */}
                <div className="space-y-2 max-h-[540px] overflow-y-auto pr-1">
                  {filteredIncidents.length === 0 ? (
                    <div className="p-6 text-center text-xs text-slate-500">
                      No incidents match the active filters.
                    </div>
                  ) : (
                    filteredIncidents.map((inc) => {
                      const isSelected = selectedIncident?.id === inc.id;
                      const sev = inc.risk_assessment?.severity || 'LOW';

                      return (
                        <div
                          key={inc.id}
                          onClick={() => setSelectedIncident(inc)}
                          className={`p-3 rounded-xl border transition cursor-pointer flex flex-col gap-1.5 ${
                            isSelected
                              ? 'bg-blue-950/40 border-blue-500/80 shadow-md ring-1 ring-blue-500/50'
                              : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-blue-400">{inc.id}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-slate-800 border border-slate-700 text-slate-300">
                              {inc.status}
                            </span>
                          </div>

                          <div className="text-xs font-semibold text-white line-clamp-1">
                            {inc.report.ward_name}
                          </div>

                          <p className="text-[11px] text-slate-400 line-clamp-2">
                            {inc.report.description}
                          </p>

                          <div className="pt-1 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                            <span className="text-slate-400">
                              Depth: <strong className="text-white">{inc.report.water_depth_cm || 0}cm</strong>
                            </span>
                            <span className="text-slate-400">
                              Risk:{' '}
                              <strong className={sev === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}>
                                {inc.risk_assessment ? `${inc.risk_assessment.risk_score}/100` : 'Pending'}
                              </strong>
                            </span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            {/* Right Column: Ward Map + Incident Detail View (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              <IncidentMap
                incidents={incidents}
                selectedIncident={selectedIncident}
                onSelectIncident={(inc) => setSelectedIncident(inc)}
              />

              <IncidentDetailView
                incident={selectedIncident}
                onAnalyze={handleAnalyze}
                onPrioritize={handlePrioritize}
                onRecommend={handleRecommend}
                onTriage={handleTriage}
                onRequestApproval={handleRequestApproval}
                onResolve={handleResolve}
                onVerify={handleVerify}
                loadingAction={loadingAction}
              />
            </div>
          </div>
        )}
      </main>

      {/* Citizen Submission Modal */}
      <IncidentReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onSubmitSuccess={handleCitizenSubmit}
      />
    </div>
  );
}
