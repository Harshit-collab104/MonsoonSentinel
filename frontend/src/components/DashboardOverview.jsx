import React from 'react';
import { Clock, Wrench, CheckCircle2, Waves } from 'lucide-react';

export default function DashboardOverview({ stats }) {
  if (!stats) return null;

  const severity = stats.severity_breakdown || {};

  return (
    <div className="h-8 min-h-[32px] max-h-[32px] bg-[#090D16] border-b border-[#1F2937] px-3 flex items-center overflow-x-auto divide-x divide-[#1F2937] text-[11px] font-mono select-none shrink-0">
      {/* Telemetry Status */}
      <div className="flex items-center gap-1.5 pr-3 shrink-0">
        <span className="w-1.5 h-1.5 bg-[#10B981] animate-pulse inline-block" />
        <span className="font-bold text-white uppercase tracking-wider text-[10px]">RADAR_TELEMETRY: LIVE</span>
      </div>

      {/* Active Incidents */}
      <div className="flex items-center gap-1.5 px-3 shrink-0 text-[#9CA3AF]">
        <span>ACTIVE:</span>
        <strong className="text-white font-bold">{stats.active_incidents ?? 0}</strong>
        <span className="text-[#374151]">/</span>
        <span className="text-[10px]">TOTAL: {stats.total_incidents ?? 0}</span>
      </div>

      {/* Critical & High Risk */}
      <div className="flex items-center gap-1.5 px-3 shrink-0">
        <span className="text-[#9CA3AF]">ALERT_TIERS:</span>
        <span className="bg-[#7F1D1D] text-[#EF4444] border border-[#EF4444] px-1 py-0.2 font-bold text-[10px]">
          {severity.CRITICAL || 0} CRIT
        </span>
        <span className="bg-[#78350F] text-[#F59E0B] border border-[#F59E0B] px-1 py-0.2 font-bold text-[10px]">
          {severity.HIGH || 0} HIGH
        </span>
      </div>

      {/* Awaiting Approval */}
      <div className="flex items-center gap-1.5 px-3 shrink-0 text-[#9CA3AF]">
        <Clock className="w-3 h-3 text-[#F59E0B]" />
        <span>PENDING_REVIEW:</span>
        <strong className="text-[#F59E0B] font-bold">{stats.awaiting_approval ?? 0}</strong>
      </div>

      {/* Crews Dispatched */}
      <div className="flex items-center gap-1.5 px-3 shrink-0 text-[#9CA3AF]">
        <Wrench className="w-3 h-3 text-[#38BDF8]" />
        <span>IN_PROGRESS:</span>
        <strong className="text-white font-bold">{stats.in_progress ?? 0}</strong>
      </div>

      {/* Telemetry Verified */}
      <div className="flex items-center gap-1.5 px-3 shrink-0 text-[#9CA3AF]">
        <CheckCircle2 className="w-3 h-3 text-[#10B981]" />
        <span>VERIFIED:</span>
        <strong className="text-[#10B981] font-bold">{stats.verified ?? 0}</strong>
      </div>

      {/* Avg Depth */}
      <div className="flex items-center gap-1.5 px-3 shrink-0 text-[#9CA3AF]">
        <Waves className="w-3 h-3 text-[#38BDF8]" />
        <span>AVG_DEPTH:</span>
        <strong className="text-[#38BDF8] font-bold">{stats.average_reported_depth_cm ?? 0}CM</strong>
      </div>

      {/* Storage Backend */}
      <div className="flex items-center gap-1.5 pl-3 shrink-0 text-[#9CA3AF]">
        <span>STORE:</span>
        <strong className="text-white uppercase">{stats.storage_backend === 'dynamodb' ? 'DYNAMODB' : 'SQLITE'}</strong>
      </div>
    </div>
  );
}
