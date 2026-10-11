import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  AlertTriangle,
  Play,
  FileCheck,
  Send,
  Sparkles,
  Info,
  History,
  Wrench,
  Check,
  RotateCcw,
  ShieldCheck,
  Ban,
  Camera,
  Upload,
  ExternalLink,
  Eye,
  Loader2
} from 'lucide-react';
import ActivityTimeline from './ActivityTimeline';
import { api } from '../services/api';

export default function IncidentDetailView({
  incident,
  onAnalyze,
  onPrioritize,
  onRecommend,
  onTriage,
  onRequestApproval,
  onResolve,
  onVerify,
  onRedispatch,
  onOverrideVerify,
  onCancelIncident,
  onUploadEvidence,
  loadingAction,
}) {
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolutionEvidence, setResolutionEvidence] = useState('');
  const [resolutionFile, setResolutionFile] = useState(null);
  const [resolutionFilePreview, setResolutionFilePreview] = useState(null);
  const [verifyFlowRate, setVerifyFlowRate] = useState(75.0);
  const [verifyDepth, setVerifyDepth] = useState(0.0);
  const [simulateVerifyFail, setSimulateVerifyFail] = useState(false);
  const [showAuditHistory, setShowAuditHistory] = useState(false);
  const [supervisorRationale, setSupervisorRationale] = useState('');
  const [supervisorName, setSupervisorName] = useState('Chief_Dispatcher_Kapoor');

  // Evidence photo state
  const [reportImageUrl, setReportImageUrl] = useState(null);
  const [taskEvidenceUrl, setTaskEvidenceUrl] = useState(null);
  const [uploadingReportPhoto, setUploadingReportPhoto] = useState(false);
  const [uploadingTaskPhoto, setUploadingTaskPhoto] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Resolve presigned URLs for S3 keys or direct URLs
  useEffect(() => {
    let isMounted = true;

    async function resolveUrls() {
      if (!incident) return;

      // 1. Resolve Report Evidence Image
      const reportImg = incident.report?.image_url;
      if (reportImg) {
        if (reportImg.startsWith('http://') || reportImg.startsWith('https://') || reportImg.startsWith('data:')) {
          if (isMounted) setReportImageUrl(reportImg);
        } else {
          // It is an S3 key
          try {
            const res = await api.getPresignedUrl(reportImg);
            if (isMounted && res.presigned_url) {
              setReportImageUrl(res.presigned_url);
            }
          } catch (err) {
            console.error('Failed to resolve report presigned URL:', err);
            if (isMounted) setReportImageUrl(null);
          }
        }
      } else {
        if (isMounted) setReportImageUrl(null);
      }

      // 2. Resolve Resolution Task Evidence Image
      const taskImg = incident.response_task?.evidence_url;
      if (taskImg) {
        if (taskImg.startsWith('http://') || taskImg.startsWith('https://') || taskImg.startsWith('data:')) {
          if (isMounted) setTaskEvidenceUrl(taskImg);
        } else {
          try {
            const res = await api.getPresignedUrl(taskImg);
            if (isMounted && res.presigned_url) {
              setTaskEvidenceUrl(res.presigned_url);
            }
          } catch (err) {
            console.error('Failed to resolve task presigned URL:', err);
            if (isMounted) setTaskEvidenceUrl(null);
          }
        }
      } else {
        if (isMounted) setTaskEvidenceUrl(null);
      }
    }

    resolveUrls();
    return () => {
      isMounted = false;
    };
  }, [incident]);

  // Handler for direct evidence photo upload from the Evidence card
  const handleDirectEvidenceUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !incident) return;

    setUploadingReportPhoto(true);
    setUploadError(null);
    try {
      if (onUploadEvidence) {
        await onUploadEvidence(incident.id, file, false);
      } else {
        await api.uploadEvidence(incident.id, file, false);
      }
    } catch (err) {
      setUploadError(err.message || 'Failed to upload photo evidence');
    } finally {
      setUploadingReportPhoto(false);
      e.target.value = '';
    }
  };

  // Handler for field resolution with optional file
  const handleResolutionSubmit = async () => {
    let finalEvidenceKey = resolutionEvidence;

    if (resolutionFile) {
      setUploadingTaskPhoto(true);
      try {
        const uploadRes = await api.uploadEvidence(incident.id, resolutionFile, true);
        finalEvidenceKey = uploadRes.s3_key || uploadRes.s3_uri;
      } catch (err) {
        alert(`Failed to upload clearance photo: ${err.message}`);
        setUploadingTaskPhoto(false);
        return;
      }
      setUploadingTaskPhoto(false);
    }

    onResolve(
      incident.id,
      resolutionNotes || 'Drain cleared and flushed by response crew.',
      finalEvidenceKey
    );
  };


  if (!incident) {
    return (
      <div className="w-full h-full p-8 text-center text-[#71717A] bg-[#09090B] flex flex-col items-center justify-center">
        <Info className="w-5 h-5 mx-auto mb-2 text-[#52525B]" />
        <p className="text-xs">Select an incident from the sidebar to inspect telemetry</p>
      </div>
    );
  }

  const risk = incident.risk_assessment;
  const task = incident.response_task;
  const verification = incident.verification;
  const status = incident.status;

  return (
    <div className="w-full bg-[#09090B] p-5 space-y-5 text-sm select-text">
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-3 pb-4 border-b border-[#27272A]">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-mono font-medium text-[#FAFAFA] bg-[#18181B] px-2 py-0.5 rounded border border-[#27272A]">
              {incident.id}
            </span>
            <span className="px-2 py-0.5 text-xs font-medium rounded bg-[#27272A] text-[#E4E4E7]">
              {status}
            </span>
            {risk?.severity && (
              <span className="px-2 py-0.5 text-xs font-medium rounded bg-[#27272A] text-[#FAFAFA] border border-[#3F3F46]">
                {risk.severity} Risk
              </span>
            )}
          </div>
          <h2 className="text-base font-semibold text-white tracking-tight">{incident.report.ward_name}</h2>
          <p className="text-xs text-[#71717A] mt-0.5">
            Reported by <span className="text-[#A1A1AA]">{incident.report.reporter_name}</span> • Landmark: {incident.report.landmark || 'N/A'}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center flex-wrap gap-2">
          {status === 'NEW' && (
            <>
              <button
                onClick={() => onAnalyze(incident.id)}
                disabled={loadingAction}
                className="h-7 px-3 bg-[#18181B] hover:bg-[#27272A] text-[#FAFAFA] border border-[#27272A] text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
              >
                <Play className="w-3 h-3 text-[#A1A1AA]" />
                <span>Calculate Risk</span>
              </button>
              <button
                onClick={() => onTriage(incident.id)}
                disabled={loadingAction}
                className="h-7 px-3 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Auto-Triage</span>
              </button>
            </>
          )}

          {status === 'ANALYZING' && (
            <button
              onClick={() => onPrioritize(incident.id)}
              disabled={loadingAction}
              className="h-7 px-3 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              <Play className="w-3 h-3" />
              <span>Prioritize</span>
            </button>
          )}

          {status === 'PRIORITIZED' && (
            <button
              onClick={() => onRecommend(incident.id)}
              disabled={loadingAction}
              className="h-7 px-3 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Recommend Response</span>
            </button>
          )}

          {status === 'RECOMMENDED' && (
            <button
              onClick={() => onRequestApproval(incident.id)}
              disabled={loadingAction}
              className="h-7 px-3 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              <FileCheck className="w-3.5 h-3.5" />
              <span>Request Dispatch</span>
            </button>
          )}

          {status === 'NEEDS_HUMAN_REVIEW' && (
            <span className="h-7 px-2.5 rounded bg-amber-950/80 text-amber-300 border border-amber-500/50 text-xs font-medium flex items-center gap-1.5 animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>Review Required</span>
            </span>
          )}

          <button
            onClick={() => setShowAuditHistory(!showAuditHistory)}
            className="h-7 px-2.5 bg-[#18181B] hover:bg-[#27272A] text-[#A1A1AA] hover:text-[#FAFAFA] border border-[#27272A] text-xs font-medium rounded transition cursor-pointer flex items-center gap-1.5"
          >
            <History className="w-3.5 h-3.5" />
            <span>{showAuditHistory ? 'Hide Audit' : 'Audit Trail'}</span>
          </button>
        </div>
      </div>

      {/* Key-Value Telemetry Strip */}
      <div className="bg-[#121214] border border-[#27272A] rounded-md p-3 text-xs flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[#A1A1AA]">
        <div>ID: <span className="font-mono text-[#FAFAFA] font-medium">{incident.id}</span></div>
        <span className="text-[#3F3F46]">/</span>
        <div>Ward: <span className="text-[#FAFAFA]">{incident.report.ward_name}</span></div>
        <span className="text-[#3F3F46]">/</span>
        <div>Water Depth: <span className="font-mono text-[#FAFAFA]">{incident.report.water_depth_cm || 0} cm</span></div>
        <span className="text-[#3F3F46]">/</span>
        <div>Drain Blockage: <span className="text-[#FAFAFA]">{incident.report.drain_blockage_level}</span></div>
        <span className="text-[#3F3F46]">/</span>
        <div>Coordinates: <span className="font-mono text-[#71717A]">{incident.report.latitude.toFixed(4)}, {incident.report.longitude.toFixed(4)}</span></div>
      </div>

      {/* Photographic Evidence Card */}
      <div className="p-3 bg-[#121214] border border-[#27272A] rounded-md space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-medium text-[#FAFAFA]">
            <Camera className="w-3.5 h-3.5 text-emerald-400" />
            <span>Photographic Evidence</span>
            {incident.report.image_url && (
              <span className="text-[10px] font-mono text-zinc-400 bg-[#18181B] px-1.5 py-0.5 rounded border border-[#27272A] truncate max-w-[180px]">
                {incident.report.image_url.startsWith('http') ? 'External URL' : incident.report.image_url}
              </span>
            )}
          </div>

          <label className="cursor-pointer inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 hover:text-emerald-300 bg-[#18181B] hover:bg-[#27272A] border border-[#27272A] px-2.5 py-1 rounded transition">
            {uploadingReportPhoto ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin text-emerald-400" />
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <Upload className="w-3 h-3" />
                <span>{incident.report.image_url ? 'Replace Photo' : 'Upload Photo'}</span>
              </>
            )}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleDirectEvidenceUpload}
              disabled={uploadingReportPhoto || loadingAction}
              className="hidden"
            />
          </label>
        </div>

        {uploadError && (
          <div className="p-2 bg-red-950/60 border border-red-800 text-red-300 rounded text-xs flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {reportImageUrl ? (
          <div className="relative group rounded overflow-hidden border border-[#27272A] bg-black">
            <img
              src={reportImageUrl}
              alt="Waterlogging evidence"
              className="w-full max-h-56 object-cover object-center transition group-hover:opacity-95"
            />
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-2 flex items-center justify-between text-[11px]">
              <span className="text-zinc-300 truncate font-mono text-[10px]">
                {incident.report.image_url}
              </span>
              <a
                href={reportImageUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 bg-black/70 px-2 py-0.5 rounded font-medium ml-2 shrink-0"
              >
                <Eye className="w-3 h-3" />
                <span>Open Full View</span>
              </a>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-[#18181B]/50 border border-dashed border-[#27272A] rounded text-center text-xs text-[#71717A]">
            <p>No photographic evidence attached yet.</p>
            <p className="text-[11px] text-[#52525B] mt-0.5">Click "Upload Photo" to attach an on-site image to S3.</p>
          </div>
        )}
      </div>

      {/* Citizen Description */}
      <div className="p-3 bg-[#121214] border border-[#27272A] rounded-md text-sm text-[#E4E4E7] space-y-1">
        <span className="font-medium text-[#71717A] block text-xs">Incident Description</span>
        <p className="text-[#D4D4D8] leading-relaxed">{incident.report.description}</p>
      </div>

      {/* Deterministic Risk Breakdown Card */}
      {risk && (
        <div className="bg-[#121214] border border-[#27272A] rounded-md p-4 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#27272A] pb-3">
            <div>
              <h3 className="text-sm font-semibold text-white">
                Risk Assessment Breakdown
              </h3>
              <p className="text-xs text-[#71717A]">Calculated deterministically by Python Risk Engine</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#A1A1AA]">Score:</span>
              <span className="text-sm font-mono font-semibold text-white bg-[#27272A] px-2.5 py-0.5 rounded border border-[#3F3F46]">
                {risk.risk_score} / 100
              </span>
            </div>
          </div>

          <div className="text-xs text-[#A1A1AA] leading-relaxed">
            <ReactMarkdown>{risk.explanation}</ReactMarkdown>
          </div>

          {/* Missing Data Flag */}
          {risk.missing_factors?.length > 0 && (
            <div className="p-2.5 bg-[#18181B] border border-[#3F3F46] rounded text-xs text-[#D4D4D8] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-[#E4E4E7]" />
              <span>
                <strong>Uncertainty Flag:</strong> Missing telemetry for [{risk.missing_factors.join(', ')}].
                +{risk.uncertainty_penalty} penalty applied.
              </span>
            </div>
          )}

          {/* Factor Breakdown Table */}
          <div className="overflow-x-auto border border-[#27272A] rounded">
            <table className="w-full text-xs border-collapse">
              <thead className="bg-[#18181B] text-[#71717A] border-b border-[#27272A]">
                <tr>
                  <th className="p-2 text-left font-medium">Factor</th>
                  <th className="p-2 text-left font-medium">Raw Value</th>
                  <th className="p-2 text-left font-medium">Weight</th>
                  <th className="p-2 text-left font-medium">Norm Score</th>
                  <th className="p-2 text-right font-medium">Contribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#27272A] text-[#A1A1AA]">
                {risk.factors.map((f, i) => (
                  <tr key={i} className="hover:bg-[#18181B]/50">
                    <td className="p-2 text-[#FAFAFA] font-medium">{f.factor_name}</td>
                    <td className="p-2 font-mono">{String(f.raw_value ?? 'N/A')}</td>
                    <td className="p-2 font-mono">{(f.weight * 100).toFixed(0)}%</td>
                    <td className="p-2 font-mono">{f.normalized_score.toFixed(1)}/100</td>
                    <td className="p-2 text-right font-mono text-[#FAFAFA]">+{f.contribution} pts</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Operational Response Dispatch Plan */}
      {(incident.recommended_action || task) && (
        <div className="bg-[#121214] border border-[#27272A] rounded-md p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[#27272A] pb-2.5">
            <div className="flex items-center gap-2">
              <Wrench className="w-4 h-4 text-[#A1A1AA]" />
              <h3 className="text-sm font-semibold text-white">
                Dispatch Plan & Assigned Task
              </h3>
            </div>
            {task && (
              <span className="text-xs text-[#71717A] font-mono">
                Task ID: <strong className="text-[#FAFAFA]">{task.task_id}</strong>
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 bg-[#18181B] border border-[#27272A] rounded">
              <span className="text-[#71717A] block text-[11px] mb-0.5">Action Type</span>
              <strong className="text-white text-xs">{task?.action_type || incident.recommended_action?.action_type}</strong>
            </div>
            <div className="p-2.5 bg-[#18181B] border border-[#27272A] rounded">
              <span className="text-[#71717A] block text-[11px] mb-0.5">Assigned Unit</span>
              <strong className="text-white text-xs">{task?.assigned_unit || incident.recommended_action?.assigned_unit}</strong>
            </div>
          </div>

          <div className="p-2.5 bg-[#18181B] border border-[#27272A] rounded text-xs text-[#A1A1AA]">
            <strong className="text-white">Operational Notice:</strong> {task?.disclaimer || incident.recommended_action?.disclaimer}
          </div>

          {/* Clearance Photo Display if attached */}
          {task?.evidence_url && (
            <div className="p-2.5 bg-[#18181B] border border-[#27272A] rounded space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#A1A1AA] flex items-center gap-1.5 font-medium">
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Field Clearance Evidence Attached</span>
                </span>
                {taskEvidenceUrl && (
                  <a
                    href={taskEvidenceUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 font-mono"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>View S3 Image</span>
                  </a>
                )}
              </div>
              {taskEvidenceUrl && (
                <div className="rounded overflow-hidden border border-[#27272A] max-h-48 bg-black">
                  <img
                    src={taskEvidenceUrl}
                    alt="Resolution clearance"
                    className="w-full max-h-48 object-cover object-center"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Step 9: In-Progress Resolution Submission */}
      {status === 'IN_PROGRESS' && (
        <div className="p-4 bg-[#121214] border border-[#27272A] rounded-md space-y-3.5 text-xs">
          <div className="flex items-center justify-between border-b border-[#27272A] pb-2">
            <h4 className="font-semibold text-white text-sm flex items-center gap-2">
              <Wrench className="w-4 h-4 text-emerald-400" />
              <span>Step 9: Submit Field Resolution Evidence</span>
            </h4>
            <span className="text-[11px] text-zinc-400 font-mono">Status: IN_PROGRESS</span>
          </div>

          <textarea
            rows={2}
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Field notes: Culvert clearance description, machinery utilized, sediment volume removed..."
            className="w-full bg-[#18181B] border border-[#27272A] rounded p-2.5 text-xs text-[#FAFAFA] placeholder-[#71717A] outline-none focus:border-[#3F3F46]"
          />

          {/* Clearance Photo Upload or Key Input */}
          <div className="space-y-2 pt-1 border-t border-[#27272A]/60">
            <label className="text-[11px] font-medium text-zinc-300 block">
              Clearance Photographic Evidence (Upload to S3 or specify key)
            </label>

            <div className="flex items-center gap-2">
              <label className="flex-1 cursor-pointer flex items-center justify-center gap-2 h-8 px-3 bg-[#18181B] hover:bg-[#27272A] border border-dashed border-[#3F3F46] rounded text-xs text-[#FAFAFA] transition">
                <Camera className="w-3.5 h-3.5 text-emerald-400" />
                <span className="truncate">
                  {resolutionFile ? resolutionFile.name : 'Choose clearance photo from disk...'}
                </span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setResolutionFile(f);
                      setResolutionFilePreview(URL.createObjectURL(f));
                    }
                  }}
                  className="hidden"
                />
              </label>

              {resolutionFile && (
                <button
                  type="button"
                  onClick={() => { setResolutionFile(null); setResolutionFilePreview(null); }}
                  className="h-8 px-2 text-xs text-zinc-400 hover:text-white bg-[#18181B] border border-[#27272A] rounded cursor-pointer"
                >
                  Clear
                </button>
              )}
            </div>

            {resolutionFilePreview && (
              <div className="relative rounded overflow-hidden border border-[#27272A] max-h-32 bg-black flex items-center justify-center">
                <img
                  src={resolutionFilePreview}
                  alt="Clearance preview"
                  className="w-full h-32 object-cover"
                />
                <span className="absolute bottom-1 right-2 bg-black/75 px-1.5 py-0.5 rounded text-[10px] text-emerald-400 font-mono">
                  Ready to attach on submit
                </span>
              </div>
            )}

            {!resolutionFile && (
              <input
                type="text"
                value={resolutionEvidence}
                onChange={(e) => setResolutionEvidence(e.target.value)}
                placeholder="Or manual clearance S3 key / URL (optional)"
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-2.5 text-xs text-[#FAFAFA] placeholder-[#71717A] outline-none focus:border-[#3F3F46]"
              />
            )}
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleResolutionSubmit}
              disabled={loadingAction || uploadingTaskPhoto}
              className="h-8 px-4 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5 shadow"
            >
              {uploadingTaskPhoto ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Uploading Evidence...</span>
                </>
              ) : (
                <>
                  <Send className="w-3 h-3 stroke-[2.5]" />
                  <span>Record Resolution & Clearance</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 10: Telemetry Verification */}
      {status === 'RESOLVED' && (
        <div className="p-4 bg-[#121214] border border-[#27272A] rounded-md space-y-3 text-xs">
          <h4 className="font-semibold text-white text-sm">
            Step 10: Automated Sensor Verification
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[#71717A] block text-xs mb-1 font-medium">Culvert Flow Rate (LPS)</label>
              <input
                type="number"
                value={verifyFlowRate}
                onChange={(e) => setVerifyFlowRate(parseFloat(e.target.value) || 0)}
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-2.5 text-[#FAFAFA] outline-none focus:border-[#3F3F46]"
              />
            </div>
            <div>
              <label className="text-[#71717A] block text-xs mb-1 font-medium">Post-Clearance Depth (CM)</label>
              <input
                type="number"
                value={verifyDepth}
                onChange={(e) => setVerifyDepth(parseFloat(e.target.value) || 0)}
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-2.5 text-[#FAFAFA] outline-none focus:border-[#3F3F46]"
              />
            </div>
          </div>
          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 text-xs text-[#A1A1AA] cursor-pointer">
              <input
                type="checkbox"
                checked={simulateVerifyFail}
                onChange={(e) => setSimulateVerifyFail(e.target.checked)}
                className="rounded"
              />
              <span>Simulate verification anomaly (NEEDS_HUMAN_REVIEW)</span>
            </label>
            <button
              onClick={() => onVerify(incident.id, verifyFlowRate, verifyDepth, simulateVerifyFail)}
              disabled={loadingAction}
              className="h-8 px-3.5 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>Verify Telemetry</span>
            </button>
          </div>
        </div>
      )}

      {/* Verification Result Display */}
      {verification && (
        <div className="p-3 bg-[#121214] border border-[#27272A] rounded-md text-xs space-y-1">
          <div className="flex items-center justify-between font-medium">
            <span className="text-[#FAFAFA]">
              Verification: {verification.verified ? 'Passed (Verified)' : 'Failed (Needs Review)'}
            </span>
            <span className="text-[#71717A]">{verification.simulated ? 'Simulated IoT' : 'Live Sensor'}</span>
          </div>
          <div className="text-[#A1A1AA]">
            <ReactMarkdown>{verification.notes}</ReactMarkdown>
          </div>
          <div className="text-[#71717A] text-[11px] pt-1">
            Culvert Flow: {verification.sensor_flow_rate_lps} L/s • Residual Depth: {verification.post_clearance_depth_cm} cm
          </div>
        </div>
      )}

      {/* Step 10b: Supervisor Review Panel for NEEDS_HUMAN_REVIEW */}
      {status === 'NEEDS_HUMAN_REVIEW' && (
        <div className="p-4 bg-[#141416] border-2 border-amber-500/70 rounded-md space-y-3.5 text-xs shadow-lg">
          <div className="flex items-center justify-between border-b border-[#27272A] pb-2.5">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Supervisor Intervention Required</span>
            </div>
            <span className="text-[11px] font-mono text-amber-300/80 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-700/40">
              ACTION_PENDING
            </span>
          </div>

          <p className="text-zinc-300 leading-relaxed text-xs">
            Automated telemetry verification flagged an anomaly (residual water depth or restricted discharge flow rate). As a supervisor, you can authorize a re-dispatch for secondary clearing, or conduct a manual field audit and override verify the incident.
          </p>

          <div className="space-y-2.5 pt-1">
            <div className="flex items-center gap-2">
              <span className="text-zinc-400 text-xs shrink-0">Reviewer:</span>
              <input
                type="text"
                value={supervisorName}
                onChange={(e) => setSupervisorName(e.target.value)}
                className="h-7 w-52 bg-[#18181B] border border-[#27272A] rounded px-2.5 text-xs text-white outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="text-zinc-400 block text-xs mb-1">Supervisor Rationale / Field Notes</label>
              <textarea
                rows={2}
                value={supervisorRationale}
                onChange={(e) => setSupervisorRationale(e.target.value)}
                placeholder="Detail secondary desilting instructions or reason for manual verification sign-off..."
                className="w-full bg-[#18181B] border border-[#27272A] rounded p-2.5 text-xs text-[#FAFAFA] placeholder-[#71717A] outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center flex-wrap gap-2 pt-1.5">
              <button
                onClick={() => onRedispatch?.(incident.id, supervisorRationale || 'Supervisor ordered crew re-dispatch and secondary desilting.', supervisorName)}
                disabled={loadingAction}
                className="h-8 px-3.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5 shadow"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Re-dispatch Crew</span>
              </button>

              <button
                onClick={() => onOverrideVerify?.(incident.id, supervisorName, supervisorRationale || 'Manual field audit confirmed blockage clear; verified by supervisor.')}
                disabled={loadingAction}
                className="h-8 px-3.5 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-semibold rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5 shadow"
              >
                <ShieldCheck className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Override & Mark Verified</span>
              </button>

              <button
                onClick={() => onCancelIncident?.(incident.id, supervisorRationale || 'Incident closed by supervisor.', supervisorName)}
                disabled={loadingAction}
                className="h-8 px-3 bg-[#18181B] hover:bg-red-950/70 hover:text-red-300 text-zinc-400 text-xs font-medium rounded border border-[#27272A] transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5 ml-auto"
              >
                <Ban className="w-3.5 h-3.5" />
                <span>Close Incident</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Audit History Timeline Toggle Section */}
      {showAuditHistory && (
        <div className="border-t border-[#27272A] pt-4">
          <ActivityTimeline auditHistory={incident.audit_history} />
        </div>
      )}
    </div>
  );
}
