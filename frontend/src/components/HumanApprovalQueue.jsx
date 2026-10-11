import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Check, X, Clock, UserCheck } from 'lucide-react';

export default function HumanApprovalQueue({ pendingIncidents, onReview, onRedispatch, onOverrideVerify, loadingAction }) {
  const [rationaleMap, setRationaleMap] = useState({});
  const [reviewerName, setReviewerName] = useState('Chief_Dispatcher_Kapoor');

  if (!pendingIncidents || pendingIncidents.length === 0) {
    return (
      <div className="bg-[#121214] border border-[#27272A] rounded-md p-10 text-center text-[#71717A]">
        <UserCheck className="w-8 h-8 mx-auto mb-2 text-[#10B981] opacity-70" />
        <h3 className="text-sm font-semibold text-[#FAFAFA]">Approval Queue Clear</h3>
        <p className="text-xs text-[#71717A] mt-1">
          No field dispatch action plans currently awaiting supervisor authorization.
        </p>
      </div>
    );
  }

  const handleRationaleChange = (incidentId, text) => {
    setRationaleMap((prev) => ({ ...prev, [incidentId]: text }));
  };

  return (
    <div className="bg-[#09090B] space-y-4 max-w-4xl mx-auto p-6">
      <div className="flex items-center justify-between pb-3 border-b border-[#27272A]">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#A1A1AA]" />
          <h2 className="text-sm font-semibold text-white">
            Supervisor Authorization Queue ({pendingIncidents.length} Pending)
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[#71717A]">Dispatcher:</span>
          <input
            type="text"
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            className="h-7 bg-[#18181B] border border-[#27272A] px-2 rounded text-white text-xs outline-none focus:border-[#3F3F46]"
          />
        </div>
      </div>

      <div className="space-y-4">
        {pendingIncidents.map((incident) => {
          const rec = incident.recommended_action || {};
          const prio = incident.priority;
          const rationale = rationaleMap[incident.id] || '';

          return (
            <div
              key={incident.id}
              className="p-4 bg-[#121214] border border-[#27272A] rounded-md space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-medium text-[#FAFAFA] bg-[#18181B] px-2 py-0.5 rounded border border-[#27272A]">
                      {incident.id}
                    </span>
                    <span className="text-sm font-semibold text-white">{incident.report.ward_name}</span>
                    {prio && (
                      <span className="text-xs text-[#A1A1AA] bg-[#18181B] px-2 py-0.5 rounded border border-[#27272A]">
                        Rank #{prio.priority_rank} • Urgency {prio.urgency_score}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-[#A1A1AA] mt-1.5 leading-relaxed">
                    <ReactMarkdown>{incident.report.description}</ReactMarkdown>
                  </div>
                </div>

                <div className="text-right sm:shrink-0">
                  <span className="text-xs text-[#71717A] block">Risk Score</span>
                  <span className="text-base font-mono font-semibold text-white">
                    {incident.risk_assessment?.risk_score || 'N/A'} / 100
                  </span>
                </div>
              </div>

              {/* Proposed Response Details or Telemetry Anomaly */}
              {incident.status === 'NEEDS_HUMAN_REVIEW' ? (
                <div className="p-3 bg-amber-950/30 border border-amber-600/40 rounded text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-amber-300 font-medium">
                    <span>Telemetry Verification Alert</span>
                    <span className="text-[10px] bg-amber-900/60 px-2 py-0.5 rounded border border-amber-500/40 font-mono">NEEDS_HUMAN_REVIEW</span>
                  </div>
                  <div className="text-zinc-300">
                    {incident.verification?.notes || 'Sensor telemetry indicates lingering water accumulation or low outflow velocity.'}
                  </div>
                  {incident.verification && (
                    <div className="text-[#A1A1AA] text-[11px] pt-1">
                      Sensor Flow: {incident.verification.sensor_flow_rate_lps} L/s • Residual Depth: {incident.verification.post_clearance_depth_cm} cm
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 bg-[#18181B] border border-[#27272A] rounded text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[#71717A]">Action Type:</span>
                    <span className="font-medium text-white">{rec.action_type || 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#71717A]">Equipment:</span>
                    <span className="text-[#E4E4E7]">{rec.equipment || 'Standard Dewatering Rig'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[#71717A]">Target Unit:</span>
                    <span className="text-[#E4E4E7]">{rec.assigned_unit || 'Municipal Sector Unit'}</span>
                  </div>
                </div>
              )}

              {/* Review Justification & Action Buttons */}
              <div className="space-y-2 pt-1">
                <input
                  type="text"
                  placeholder={
                    incident.status === 'NEEDS_HUMAN_REVIEW'
                      ? "Supervisor review rationale (e.g. Authorized secondary desilting or manual sign-off)..."
                      : "Supervisor review rationale (e.g. Authorized immediate deployment)..."
                  }
                  value={rationale}
                  onChange={(e) => handleRationaleChange(incident.id, e.target.value)}
                  className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-xs text-white placeholder-[#71717A] outline-none focus:border-[#3F3F46]"
                />

                <div className="flex items-center justify-between gap-2 pt-1">
                  <span className="text-[11px] text-[#71717A]">
                    {incident.status === 'NEEDS_HUMAN_REVIEW'
                      ? "* Manual sign-off archives telemetry; re-dispatch deploys secondary crews."
                      : "* Authorization creates an active dispatch task for field crews."}
                  </span>
                  <div className="flex items-center gap-2">
                    {incident.status === 'NEEDS_HUMAN_REVIEW' ? (
                      <>
                        <button
                          onClick={() =>
                            onRedispatch
                              ? onRedispatch(
                                  incident.id,
                                  rationale || 'Supervisor ordered crew re-dispatch.',
                                  reviewerName
                                )
                              : onReview(incident.id, false, reviewerName, rationale || 'Re-dispatch requested.')
                          }
                          disabled={loadingAction}
                          className="h-7 px-3 bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium rounded transition cursor-pointer flex items-center gap-1 shadow"
                        >
                          <span>Re-dispatch Crew</span>
                        </button>
                        <button
                          onClick={() =>
                            onOverrideVerify
                              ? onOverrideVerify(
                                  incident.id,
                                  reviewerName,
                                  rationale || 'Supervisor override: Site verified clear.'
                                )
                              : onReview(incident.id, true, reviewerName, rationale || 'Override verified.')
                          }
                          disabled={loadingAction}
                          className="h-7 px-3.5 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition cursor-pointer flex items-center gap-1 shadow"
                        >
                          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                          <span>Override & Verify</span>
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() =>
                            onReview(
                              incident.id,
                              false,
                              reviewerName,
                              rationale || 'Rejected by supervisor.'
                            )
                          }
                          disabled={loadingAction}
                          className="h-7 px-3 bg-[#18181B] hover:bg-[#27272A] text-[#A1A1AA] hover:text-white border border-[#27272A] text-xs font-medium rounded transition cursor-pointer flex items-center gap-1"
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
                          className="h-7 px-3.5 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition cursor-pointer flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                          <span>Authorize & Dispatch</span>
                        </button>
                      </>
                    )}
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

