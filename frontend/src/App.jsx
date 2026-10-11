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
  const [activeTab, setActiveTab] = useState('console'); // 'console', 'map', 'queue'
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showDetailDrawer, setShowDetailDrawer] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Agent Chat State
  const [chatLog, setChatLog] = useState([
    {
      role: 'assistant',
      content:
        'Welcome to **Monsoon Sentinel**.\n\nI am the autonomous emergency dispatcher orchestrating municipal waterlogging risk analysis and response.\n\nSelect an incident from the roster to inspect deterministic risk scores, request equipment dispatch, or verify post-clearance culvert telemetry.',
      reasoning_summary: 'Deterministic risk engine and authoritative persistence connected.'
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
      const updated = await api.getIncident(incidentId);
      setSelectedIncident(updated);
      await fetchData();

      setChatLog((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.response || `Completed automated triage for ${incidentId}.`,
          incident_id: result.incident_id,
          incident_status: result.incident_status,
          risk_score: result.risk_score,
          severity: result.severity,
          reasoning_summary: result.reasoning_summary,
          recommendations: result.recommendations,
          actions_taken: result.actions_taken,
          next_steps: result.next_steps,
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

  const handleRedispatch = async (incidentId, reason, reviewer) => {
    setLoadingAction(true);
    try {
      const updated = await api.redispatchIncident(incidentId, { reason, reviewer });
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error re-dispatching crew: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleOverrideVerify = async (incidentId, reviewer, rationale) => {
    setLoadingAction(true);
    try {
      const updated = await api.overrideVerifyIncident(incidentId, { reviewer, rationale });
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error overriding verification: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCancelIncident = async (incidentId, reason, reviewer) => {
    setLoadingAction(true);
    try {
      const updated = await api.cancelIncident(incidentId, { reason, reviewer });
      setSelectedIncident(updated);
      await fetchData();
    } catch (err) {
      alert(`Error closing incident: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCitizenSubmit = async (formData, selectedFile) => {
    const created = await api.submitReport(formData);
    if (selectedFile) {
      try {
        await api.uploadEvidence(created.id, selectedFile, false);
      } catch (uploadErr) {
        console.error('Evidence upload failed after creation:', uploadErr);
      }
    }
    await fetchData();
    const refreshed = await api.getIncident(created.id);
    setSelectedIncident(refreshed);
  };

  const handleUploadEvidence = async (incidentId, file, attachToTask = false) => {
    setLoadingAction(true);
    try {
      await api.uploadEvidence(incidentId, file, attachToTask);
      await fetchData();
      const refreshed = await api.getIncident(incidentId);
      setSelectedIncident(refreshed);
    } catch (err) {
      alert(`Error uploading evidence: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleArchiveIncident = async (incidentId) => {
    setLoadingAction(true);
    try {
      const res = await api.archiveIncident(incidentId);
      alert(`Incident ${incidentId} successfully archived to S3 (${res.s3_archive_key}) and purged from active database.`);
      setSelectedIncident(null);
      await fetchData();
    } catch (err) {
      alert(`Error archiving incident: ${err.message}`);
    } finally {
      setLoadingAction(false);
    }
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
          incident_id: res.incident_id,
          incident_status: res.incident_status,
          risk_score: res.risk_score,
          severity: res.severity,
          reasoning_summary: res.reasoning_summary,
          recommendations: res.recommendations,
          actions_taken: res.actions_taken,
          next_steps: res.next_steps,
        },
      ]);
      await fetchData();
    } catch (err) {
      setChatLog((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Incident Operations Notice: ${err.message}`,
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
      (statusFilter === 'AWAITING_APPROVAL' && (i.status === 'AWAITING_APPROVAL' || i.status === 'NEEDS_HUMAN_REVIEW')) ||
      (statusFilter === 'CRITICAL' && (i.risk_assessment?.severity === 'CRITICAL' || i.risk_assessment?.severity === 'HIGH'));

    const matchesSearch =
      i.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      i.report.ward_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      i.report.description.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const pendingApprovalIncidents = incidents.filter(
    (i) => i.status === 'AWAITING_APPROVAL' || i.status === 'NEEDS_HUMAN_REVIEW'
  );

  return (
    <div className="h-screen w-screen bg-[#09090B] text-[#FAFAFA] flex flex-col font-sans overflow-hidden select-none">
      {/* Minimal Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        pendingCount={pendingApprovalIncidents.length}
        onOpenReportModal={() => setIsReportModalOpen(true)}
      />

      {/* Main Viewport Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* VIEW 1: CONSOLE MODE (Default Linear Chat + Ultra-thin 240px Sidebar) */}
        {activeTab === 'console' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Ultra-thin 240px Collapsible Sidebar */}
            <aside
              className={`${
                isSidebarOpen ? 'w-60' : 'w-0'
              } shrink-0 h-full flex flex-col bg-[#09090B] border-r border-[#27272A] transition-all duration-200 overflow-hidden relative`}
            >
              {/* Sidebar Header & Search */}
              <div className="p-2.5 border-b border-[#27272A] space-y-2 shrink-0">
                <div className="flex items-center justify-between text-xs font-medium text-[#A1A1AA]">
                  <span className="flex items-center gap-1.5 text-zinc-300">
                    <Droplets className="w-3.5 h-3.5 text-[#10B981]" />
                    <span>Incidents ({filteredIncidents.length})</span>
                  </span>
                  <button
                    onClick={() => setIsSidebarOpen(false)}
                    title="Collapse sidebar"
                    className="text-[#71717A] hover:text-white p-0.5 rounded cursor-pointer text-xs"
                  >
                    ‹
                  </button>
                </div>

                {/* Minimal Search Input */}
                <div className="relative">
                  <Search className="w-3 h-3 text-[#71717A] absolute left-2 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search ward, id..."
                    className="w-full h-7 bg-[#18181B] border border-[#27272A] rounded pl-6 pr-2 text-xs text-zinc-200 placeholder-[#71717A] outline-none focus:border-[#3F3F46]"
                  />
                </div>

                {/* Filter Tabs */}
                <div className="flex items-center gap-1 overflow-x-auto text-[11px]">
                  {['ALL', 'ACTIVE', 'APPROVAL', 'CRITICAL'].map((f) => (
                    <button
                      key={f}
                      onClick={() => setStatusFilter(f === 'APPROVAL' ? 'AWAITING_APPROVAL' : f)}
                      className={`h-5 px-1.5 rounded text-[10px] font-medium transition cursor-pointer ${
                        (f === 'APPROVAL' && statusFilter === 'AWAITING_APPROVAL') || statusFilter === f
                          ? 'bg-[#27272A] text-white'
                          : 'text-[#71717A] hover:text-zinc-300'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>

              {/* Roster List */}
              <div className="flex-1 overflow-y-auto divide-y divide-[#18181B]">
                {filteredIncidents.length === 0 ? (
                  <div className="p-4 text-center text-xs text-[#71717A]">No matching incidents</div>
                ) : (
                  filteredIncidents.map((inc) => {
                    const isSelected = selectedIncident?.id === inc.id;
                    const sev = inc.risk_assessment?.severity || 'LOW';

                    return (
                      <div
                        key={inc.id}
                        onClick={() => setSelectedIncident(inc)}
                        className={`p-2.5 transition cursor-pointer text-xs ${
                          isSelected
                            ? 'bg-[#18181B] text-white border-l-2 border-[#10B981]'
                            : 'text-[#A1A1AA] hover:bg-[#121214] hover:text-zinc-200 border-l-2 border-transparent'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono text-[11px] font-medium text-zinc-300 truncate max-w-[130px]">
                            {inc.report.ward_name}
                          </span>
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                              inc.status === 'AWAITING_APPROVAL'
                                ? 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
                                : inc.status === 'VERIFIED' || inc.status === 'RESOLVED'
                                ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                                : sev === 'CRITICAL'
                                ? 'bg-rose-950/60 text-rose-400 border border-rose-800/60'
                                : 'bg-[#27272A] text-[#A1A1AA]'
                            }`}
                          >
                            {inc.status === 'AWAITING_APPROVAL' ? 'APPROVAL' : inc.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#71717A] line-clamp-1 mb-1">
                          {inc.report.description}
                        </p>
                        <div className="flex items-center justify-between text-[10px] text-[#71717A] font-mono">
                          <span>{inc.report.water_depth_cm || 0}cm depth</span>
                          <span
                            className={
                              sev === 'CRITICAL'
                                ? 'text-rose-400'
                                : sev === 'HIGH'
                                ? 'text-amber-400'
                                : 'text-zinc-400'
                            }
                          >
                            {inc.risk_assessment ? `${inc.risk_assessment.risk_score} score` : '—'}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </aside>

            {/* Sidebar Reopen Tab if collapsed */}
            {!isSidebarOpen && (
              <button
                onClick={() => setIsSidebarOpen(true)}
                title="Expand incident roster"
                className="w-6 h-full border-r border-[#27272A] flex items-center justify-center text-xs text-[#71717A] hover:text-white bg-[#09090B] hover:bg-[#18181B] transition cursor-pointer"
              >
                ›
              </button>
            )}

            {/* Center Area: Clean Full-Width Terminal with Floating Details Drawer Toggle */}
            <main className="flex-1 h-full overflow-hidden flex flex-col relative bg-[#09090B]">
              {/* Optional Top Bar for Selected Incident Context & Details Drawer Button */}
              {selectedIncident && (
                <div className="h-9 px-4 border-b border-[#27272A] flex items-center justify-between bg-[#09090B] text-xs text-[#A1A1AA] shrink-0">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-400">Context:</span>
                    <span className="font-medium text-white font-mono">{selectedIncident.id}</span>
                    <span className="text-[#52525B]">·</span>
                    <span className="text-zinc-300">{selectedIncident.report.ward_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowDetailDrawer(!showDetailDrawer)}
                      className={`px-2.5 py-0.5 rounded text-xs transition cursor-pointer border ${
                        showDetailDrawer
                          ? 'bg-[#27272A] text-white border-[#3F3F46]'
                          : 'text-[#A1A1AA] hover:text-white border-transparent hover:border-[#27272A]'
                      }`}
                    >
                      {showDetailDrawer ? 'Hide Details' : 'View Details & Actions'}
                    </button>
                  </div>
                </div>
              )}

              <div className="flex-1 flex overflow-hidden">
                {/* Clean Terminal Console */}
                <div className="flex-1 h-full overflow-hidden">
                  <AgentChatConsole
                    selectedIncident={selectedIncident}
                    onSendMessage={handleSendMessage}
                    chatLog={chatLog}
                    loadingChat={loadingChat}
                  />
                </div>

                {/* Collapsible Right Inspector for Incident Operations & Verification */}
                {showDetailDrawer && selectedIncident && (
                  <aside className="w-[460px] xl:w-[500px] shrink-0 h-full border-l border-[#27272A] overflow-y-auto bg-[#09090B] animate-in slide-in-from-right duration-200">
                    <div className="p-3 border-b border-[#27272A] flex items-center justify-between">
                      <span className="text-xs font-medium text-zinc-300">Incident Details</span>
                      <button
                        onClick={() => setShowDetailDrawer(false)}
                        className="text-xs text-[#71717A] hover:text-white p-1"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="p-2">
                      <IncidentDetailView
                        incident={selectedIncident}
                        onAnalyze={handleAnalyze}
                        onPrioritize={handlePrioritize}
                        onRecommend={handleRecommend}
                        onTriage={handleTriage}
                        onRequestApproval={handleRequestApproval}
                        onResolve={handleResolve}
                        onVerify={handleVerify}
                        onRedispatch={handleRedispatch}
                        onOverrideVerify={handleOverrideVerify}
                        onCancelIncident={handleCancelIncident}
                        onUploadEvidence={handleUploadEvidence}
                        onArchive={handleArchiveIncident}
                        loadingAction={loadingAction}
                      />
                    </div>
                  </aside>
                )}
              </div>
            </main>
          </div>
        )}

        {/* VIEW 2: MAP MODE (Interactive GIS Radar + Generous Telemetry & Operations Panel) */}
        {activeTab === 'map' && (
          <div className="flex-1 flex overflow-hidden">
            {/* GIS Grid Canvas */}
            <div className="flex-1 h-full overflow-hidden relative">
              <IncidentMap
                incidents={incidents}
                selectedIncident={selectedIncident}
                onSelectIncident={(inc) => setSelectedIncident(inc)}
              />
            </div>

            {/* Generous Telemetry & Operations Sidebar */}
            <aside className="w-[460px] xl:w-[500px] shrink-0 h-full border-l border-[#27272A] bg-[#09090B] flex flex-col overflow-hidden shadow-2xl">
              <div className="p-3 border-b border-[#27272A] flex items-center justify-between text-xs font-medium text-zinc-300">
                <span>Selected Culvert Telemetry & Ops</span>
                {selectedIncident && (
                  <span className="text-[10px] font-mono text-[#71717A]">{selectedIncident.id}</span>
                )}
              </div>
              <div className="flex-1 overflow-y-auto p-2">
                {selectedIncident ? (
                  <IncidentDetailView
                    incident={selectedIncident}
                    onAnalyze={handleAnalyze}
                    onPrioritize={handlePrioritize}
                    onRecommend={handleRecommend}
                    onTriage={handleTriage}
                    onRequestApproval={handleRequestApproval}
                    onResolve={handleResolve}
                    onVerify={handleVerify}
                    onRedispatch={handleRedispatch}
                    onOverrideVerify={handleOverrideVerify}
                    onCancelIncident={handleCancelIncident}
                    onUploadEvidence={handleUploadEvidence}
                    onArchive={handleArchiveIncident}
                    loadingAction={loadingAction}
                  />
                ) : (
                  <div className="p-6 text-center text-xs text-[#71717A]">
                    Click any marker on the map to inspect water levels and sensors.
                  </div>
                )}
              </div>
            </aside>
          </div>
        )}

        {/* VIEW 3: SUPERVISOR QUEUE MODE */}
        {activeTab === 'queue' && (
          <div className="flex-1 h-full overflow-y-auto bg-[#09090B] p-6 max-w-4xl mx-auto">
            <HumanApprovalQueue
              pendingIncidents={pendingApprovalIncidents}
              onReview={handleHumanReview}
              onRedispatch={handleRedispatch}
              onOverrideVerify={handleOverrideVerify}
              loadingAction={loadingAction}
            />
          </div>
        )}
      </div>

      {/* Citizen Submission Modal */}
      <IncidentReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onSubmitSuccess={handleCitizenSubmit}
      />
    </div>
  );
}
