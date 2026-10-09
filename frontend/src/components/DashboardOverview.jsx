import React from 'react';
import { AlertOctagon, Clock, Wrench, CheckCircle2, Waves, ShieldAlert, BarChart3 } from 'lucide-react';

export default function DashboardOverview({ stats }) {
  if (!stats) return null;

  const severity = stats.severity_breakdown || {};
  const criticalCount = (severity.CRITICAL || 0) + (severity.HIGH || 0);

  const cards = [
    {
      title: 'Active Incidents',
      value: stats.active_incidents ?? 0,
      subtext: `Total logged: ${stats.total_incidents ?? 0}`,
      icon: AlertOctagon,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      title: 'High / Critical Risk',
      value: criticalCount,
      subtext: `Critical: ${severity.CRITICAL || 0} | High: ${severity.HIGH || 0}`,
      icon: ShieldAlert,
      color: 'text-red-400',
      bg: 'bg-red-500/10 border-red-500/20'
    },
    {
      title: 'Awaiting Human Approval',
      value: stats.awaiting_approval ?? 0,
      subtext: 'Requires supervisor sign-off',
      icon: Clock,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20'
    },
    {
      title: 'Field Crews Active',
      value: stats.in_progress ?? 0,
      subtext: 'Physical clearance ongoing',
      icon: Wrench,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20'
    },
    {
      title: 'Telemetry Verified',
      value: stats.verified ?? 0,
      subtext: `Resolved: ${stats.resolved ?? 0}`,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      title: 'Avg Water Depth',
      value: `${stats.average_reported_depth_cm ?? 0} cm`,
      subtext: 'Across reported hot-spots',
      icon: Waves,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    }
  ];

  return (
    <div className="space-y-4">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border backdrop-blur ${card.bg} flex flex-col justify-between transition hover:scale-[1.01]`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-300 line-clamp-1">{card.title}</span>
                <Icon className={`w-4 h-4 ${card.color}`} />
              </div>
              <div>
                <div className={`text-2xl font-bold tracking-tight ${card.color}`}>{card.value}</div>
                <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{card.subtext}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Severity Breakdown Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-300 font-medium">
          <BarChart3 className="w-4 h-4 text-slate-400" />
          <span>Dynamic Risk Tiers:</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2.5 py-1 rounded-md bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
            Critical: {severity.CRITICAL || 0}
          </span>
          <span className="px-2.5 py-1 rounded-md bg-orange-500/10 text-orange-400 border border-orange-500/20 font-medium">
            High: {severity.HIGH || 0}
          </span>
          <span className="px-2.5 py-1 rounded-md bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 font-medium">
            Medium: {severity.MEDIUM || 0}
          </span>
          <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            Low: {severity.LOW || 0}
          </span>
          {stats.needs_human_review > 0 && (
            <span className="px-2.5 py-1 rounded-md bg-pink-500/10 text-pink-400 border border-pink-500/20 font-medium animate-pulse">
              Needs Review: {stats.needs_human_review}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
