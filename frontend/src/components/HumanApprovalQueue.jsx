import React, { useState } from 'react';
import { Check, X, ShieldAlert, AlertTriangle, Clock, UserCheck, Wrench } from 'lucide-react';

export default function HumanApprovalQueue({ pendingIncidents, onReview, loadingAction }) {
  const [rationaleMap, setRationaleMap] = useState({});
  const [reviewerName, setReviewerName] = useState('Chief_Dispatcher_Kapoor');

  if (!pendingIncidents || pendingIncidents.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-slate-400">
        <UserCheck className="w-8 h-8 mx-auto mb-2 text-emerald-400 opacity-60" />
        <h3 className="text-sm font-semibold text-slate-300">Approval Queue Clear</h3>
        <p className="text-xs text-slate-500 mt-1">
          No response plans currently awaiting human supervisor authorization.
        </p>
      </div>
    );
  }

  const handleRationaleChange = (incidentId, text) => {
    setRationaleMap((prev) => ({ ...prev, [incidentId]: text }));
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-purple-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Human Supervisor Authorization Queue ({pendingIncidents.length} Pending)
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400">Reviewer:</span>
          <input
            type="text"
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono text-xs outline-none"
          />
        </div>
      </div>

      <div className="space-y-3">
        {pendingIncidents.map((incident) => {
          const rec = incident.recommended_action || {};
          const prio = incident.priority;
          const rationale = rationaleMap[incident.id] || '';

          return (
            <div
              key={incident.id}
              className="p-4 rounded-xl bg-slate-950/80 border border-purple-500/30 space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                      {incident.id}
                    </span>
                    <span className="text-xs font-bold text-white">{incident.report.ward_name}</span>
                    {prio && (
                      <span className="text-[11px] font-mono text-amber-400 font-bold bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                        Rank #{prio.priority_rank} (Urgency: {prio.urgency_score})
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{incident.report.description}</p>
                </div>

                <div className="text-right sm:shrink-0">
                  <span className="text-xs text-slate-400 block">Risk Score:</span>
                  <span className="text-base font-extrabold text-amber-400 font-mono">
                    {incident.risk_assessment?.risk_score || 'N/A'}/100
                  </span>
                </div>
              </div>

              {/* Proposed Response Details */}
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Proposed Action:</span>
                  <span className="font-mono font-bold text-purple-300">{rec.action_type || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Equipment:</span>
                  <span className="text-slate-200">{rec.equipment || 'Standard Dewatering Rig'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Target Unit:</span>
                  <span className="text-slate-200">{rec.assigned_unit || 'Municipal Sector Unit'}</span>
                </div>
              </div>

              {/* Review Justification Input & Action Buttons */}
              <div className="space-y-2 pt-1">
                <input
                  type="text"
                  placeholder="Supervisor review rationale (e.g. Critical access road confirmed, authorized dispatch)..."
                  value={rationale}
                  onChange={(e) => handleRationaleChange(incident.id, e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-purple-500"
                />

                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] text-slate-500">
                    * Approving will dispatch the task to field crews.
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() =>
                        onReview(
                          incident.id,
                          false,
                          reviewerName,
                          rationale || 'Rejected by supervisor due to misclassified priority.'
                        )
                      }
                      disabled={loadingAction}
                      className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium flex items-center gap-1 transition cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject Plan</span>
                    </button>
                    <button
                      onClick={() =>
                        onReview(
                          incident.id,
                          true,
                          reviewerName,
                          rationale || 'Authorized immediate response team deployment.'
                        )
                      }
                      disabled={loadingAction}
                      className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 shadow transition cursor-pointer"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Authorize & Dispatch Task</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
