import React, { useState } from 'react';
import {
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Play,
  FileCheck,
  Send,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Info,
  Waves,
  Cpu,
  History
} from 'lucide-react';
import ActivityTimeline from './ActivityTimeline';

export default function IncidentDetailView({
  incident,
  onAnalyze,
  onPrioritize,
  onRecommend,
  onTriage,
  onRequestApproval,
  onResolve,
  onVerify,
  loadingAction,
}) {
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolutionEvidence, setResolutionEvidence] = useState('');
  const [verifyFlowRate, setVerifyFlowRate] = useState(75.0);
  const [verifyDepth, setVerifyDepth] = useState(0.0);
  const [simulateVerifyFail, setSimulateVerifyFail] = useState(false);
  const [showAuditHistory, setShowAuditHistory] = useState(false);

  if (!incident) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-400">
        <Info className="w-8 h-8 mx-auto mb-2 text-slate-500 opacity-60" />
        <p className="text-sm">Select an incident from the list or map to inspect details and risk calculation.</p>
      </div>
    );
  }

  const risk = incident.risk_assessment;
  const task = incident.response_task;
  const verification = incident.verification;
  const status = incident.status;

  const getStatusBadge = (st) => {
    const map = {
      NEW: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      ANALYZING: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 animate-pulse',
      PRIORITIZED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      RECOMMENDED: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      AWAITING_APPROVAL: 'bg-purple-600/20 text-purple-300 border-purple-500/30 font-bold',
      APPROVED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      IN_PROGRESS: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      RESOLVED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      VERIFIED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 font-bold',
      REJECTED: 'bg-red-500/10 text-red-400 border-red-500/20',
      CANCELLED: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      NEEDS_HUMAN_REVIEW: 'bg-pink-500/20 text-pink-300 border-pink-500/30 animate-pulse font-bold',
    };
    return map[st] || 'bg-slate-800 text-slate-300 border-slate-700';
  };

  const getSeverityBadge = (sev) => {
    if (sev === 'CRITICAL') return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (sev === 'HIGH') return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    if (sev === 'MEDIUM') return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
    return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl space-y-6 p-6">
      {/* Incident Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              {incident.id}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs border font-medium ${getStatusBadge(status)}`}>
              {status}
            </span>
            {risk?.severity && (
              <span className={`px-2 py-0.5 rounded-full text-xs border font-medium ${getSeverityBadge(risk.severity)}`}>
                {risk.severity} Risk
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">{incident.report.ward_name}</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Reported by <span className="text-slate-200">{incident.report.reporter_name}</span> • Landmark: {incident.report.landmark || 'N/A'}
          </p>
        </div>

        {/* Workflow Action Bar */}
        <div className="flex items-center flex-wrap gap-2">
          {status === 'NEW' && (
            <>
              <button
                onClick={() => onAnalyze(incident.id)}
                disabled={loadingAction}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Calculate Risk</span>
              </button>
              <button
                onClick={() => onTriage(incident.id)}
                disabled={loadingAction}
                className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-medium flex items-center gap-1.5 transition shadow disabled:opacity-50 cursor-pointer"
                title="Runs Strands Agent pipeline end-to-end"
              >
                <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                <span>Agent Auto-Triage</span>
              </button>
            </>
          )}

          {status === 'ANALYZING' && (
            <button
              onClick={() => onPrioritize(incident.id)}
              disabled={loadingAction}
              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Prioritize Incident</span>
            </button>
          )}

          {status === 'PRIORITIZED' && (
            <button
              onClick={() => onRecommend(incident.id)}
              disabled={loadingAction}
              className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Recommend Response</span>
            </button>
          )}

          {status === 'RECOMMENDED' && (
            <button
              onClick={() => onRequestApproval(incident.id)}
              disabled={loadingAction}
              className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
            >
              <FileCheck className="w-3.5 h-3.5" />
              <span>Submit for Human Approval</span>
            </button>
          )}

          <button
            onClick={() => setShowAuditHistory(!showAuditHistory)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition cursor-pointer"
          >
            <History className="w-3.5 h-3.5" />
            <span>{showAuditHistory ? 'Hide Audit' : 'Audit Trail'}</span>
          </button>
        </div>
      </div>

      {/* Citizen Report Description & Visual Evidence */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
        <div className="md:col-span-2 space-y-2">
          <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Citizen Description</div>
          <p className="text-xs text-slate-200 leading-relaxed">{incident.report.description}</p>
          <div className="pt-2 flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <span>Water Depth: <strong className="text-white">{incident.report.water_depth_cm || 0} cm</strong></span>
            <span>•</span>
            <span>Blockage: <strong className="text-white">{incident.report.drain_blockage_level}</strong></span>
            <span>•</span>
            <span>Coordinates: <strong className="font-mono text-slate-300">{incident.report.latitude.toFixed(4)}, {incident.report.longitude.toFixed(4)}</strong></span>
          </div>
        </div>
        {incident.report.image_url && (
          <div className="rounded-lg overflow-hidden border border-slate-800 max-h-28">
            <img
              src={incident.report.image_url}
              alt="Report evidence"
              className="w-full h-full object-cover"
            />
          </div>
        )}
      </div>

      {/* Deterministic Risk Breakdown Card */}
      {risk && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Deterministic Risk Engine Assessment
              </h3>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Calculated Score:</span>
              <span className="font-mono text-base font-extrabold text-amber-400">
                {risk.risk_score} / 100
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-900/30 text-xs text-blue-200 leading-relaxed">
            {risk.explanation}
          </div>

          {/* Missing Data Warning */}
          {risk.missing_factors?.length > 0 && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                <strong>Uncertainty Flag:</strong> Missing telemetry for [{risk.missing_factors.join(', ')}].
                Added +{risk.uncertainty_penalty} penalty to reflect unconfirmed risk.
              </span>
            </div>
          )}

          {/* Factor Breakdown List */}
          <div className="space-y-2.5">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Factor Weighting & Normalized Contributions
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {risk.factors.map((f, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-200">{f.factor_name}</span>
                    <span className="font-mono font-bold text-amber-400">+{f.contribution} pts</span>
                  </div>
                  {/* Progress Bar */}
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, f.normalized_score)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Raw: {String(f.raw_value ?? 'N/A')}</span>
                    <span>Weight: {(f.weight * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-[11px] text-slate-500 italic">
            🛡️ AI Guardrail: Calculated deterministically by the Python Risk Engine formula. The AI model does not determine risk scores or fabricate telemetry values.
          </div>
        </div>
      )}

      {/* Response Recommendation & Dispatch Task */}
      {(incident.recommended_action || task) && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Operational Response Dispatch Plan
              </h3>
            </div>
            {task && (
              <span className="font-mono text-xs text-slate-400">
                Task ID: <strong className="text-slate-200">{task.task_id}</strong>
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400 block text-[11px]">Action Type:</span>
              <strong className="text-white font-mono">{task?.action_type || incident.recommended_action?.action_type}</strong>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400 block text-[11px]">Assigned Unit:</span>
              <strong className="text-white">{task?.assigned_unit || incident.recommended_action?.assigned_unit}</strong>
            </div>
          </div>

          {/* Strict Disclaimer Notice */}
          <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-900/40 text-xs text-blue-300">
            <strong>Notice:</strong> {task?.disclaimer || incident.recommended_action?.disclaimer}
          </div>
        </div>
      )}

      {/* Step 9: In-Progress Resolution Submission */}
      {status === 'IN_PROGRESS' && (
        <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-800/40 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-300">
            Step 9: Submit Field Resolution Evidence
          </h4>
          <textarea
            rows={2}
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Field notes: Describe culvert clearance, equipment used, cubic meters of silt extracted..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:border-cyan-500 outline-none"
          />
          <div className="flex items-center gap-2">
            <input
              type="url"
              value={resolutionEvidence}
              onChange={(e) => setResolutionEvidence(e.target.value)}
              placeholder="Clearance photo URL (optional)"
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 outline-none"
            />
            <button
              onClick={() => onResolve(incident.id, resolutionNotes || 'Drain cleared and flushed by response crew.', resolutionEvidence)}
              disabled={loadingAction}
              className="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Record Resolution</span>
            </button>
          </div>
        </div>
      )}

      {/* Step 10: Telemetry Verification */}
      {status === 'RESOLVED' && (
        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-800/40 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
            Step 10: Automated Telemetry Verification
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-400 block text-[11px] mb-1">Culvert Flow Rate (LPS)</label>
              <input
                type="number"
                value={verifyFlowRate}
                onChange={(e) => setVerifyFlowRate(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white"
              />
            </div>
            <div>
              <label className="text-slate-400 block text-[11px] mb-1">Post-Clearance Depth (cm)</label>
              <input
                type="number"
                value={verifyDepth}
                onChange={(e) => setVerifyDepth(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white"
              />
            </div>
          </div>
          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={simulateVerifyFail}
                onChange={(e) => setSimulateVerifyFail(e.target.checked)}
                className="rounded text-red-500"
              />
              <span className="text-slate-400">Simulate verification failure (transitions to NEEDS_HUMAN_REVIEW)</span>
            </label>
            <button
              onClick={() => onVerify(incident.id, verifyFlowRate, verifyDepth, simulateVerifyFail)}
              disabled={loadingAction}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verify Telemetry</span>
            </button>
          </div>
        </div>
      )}

      {/* Verification Result Display */}
      {verification && (
        <div className={`p-4 rounded-xl border text-xs space-y-1 ${
          verification.verified
            ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
            : 'bg-pink-950/20 border-pink-500/30 text-pink-300'
        }`}>
          <div className="flex items-center justify-between font-bold">
            <span>Verification Status: {verification.verified ? 'PASSED (VERIFIED)' : 'FAILED (NEEDS_HUMAN_REVIEW)'}</span>
            <span className="text-[11px] font-normal text-slate-400">Mode: {verification.simulated ? 'Simulated IoT Feed' : 'Live IoT'}</span>
          </div>
          <p className="text-slate-200">{verification.notes}</p>
          <div className="text-[11px] text-slate-400 pt-1">
            Flow Rate: {verification.sensor_flow_rate_lps} L/s • Residual Depth: {verification.post_clearance_depth_cm} cm
          </div>
        </div>
      )}

      {/* Audit History Timeline Toggle Section */}
      {showAuditHistory && (
        <div className="border-t border-slate-800 pt-4">
          <ActivityTimeline auditHistory={incident.audit_history} />
        </div>
      )}
    </div>
  );
}
