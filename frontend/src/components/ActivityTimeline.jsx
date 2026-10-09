import React from 'react';
import { History, User, Cpu, ShieldCheck, Check, AlertCircle, Wrench, Shield } from 'lucide-react';

export default function ActivityTimeline({ auditHistory }) {
  if (!auditHistory || auditHistory.length === 0) {
    return (
      <div className="p-4 text-center text-xs text-slate-500">
        No audit history records available.
      </div>
    );
  }

  const getActorIcon = (actor) => {
    if (actor.includes('citizen')) return <User className="w-3.5 h-3.5 text-blue-400" />;
    if (actor.includes('risk_engine')) return <Cpu className="w-3.5 h-3.5 text-purple-400" />;
    if (actor.includes('strands_agent')) return <Cpu className="w-3.5 h-3.5 text-indigo-400" />;
    if (actor.includes('supervisor')) return <Shield className="w-3.5 h-3.5 text-emerald-400" />;
    if (actor.includes('crew')) return <Wrench className="w-3.5 h-3.5 text-cyan-400" />;
    if (actor.includes('verification')) return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />;
    return <History className="w-3.5 h-3.5 text-slate-400" />;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <History className="w-4 h-4 text-slate-400" />
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Immutable Audit History & Activity Log ({auditHistory.length} events)
        </h4>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {auditHistory.map((item, index) => {
          const date = new Date(item.timestamp);
          const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

          return (
            <div key={index} className="relative group">
              {/* Dot */}
              <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center">
                {getActorIcon(item.actor)}
              </div>

              {/* Event Content */}
              <div className="bg-slate-900/90 border border-slate-800/80 rounded-xl p-3 space-y-1 hover:border-slate-700 transition">
                <div className="flex flex-wrap items-center justify-between gap-1 text-[11px]">
                  <span className="font-mono font-bold text-slate-200 uppercase tracking-wider">
                    {item.action}
                  </span>
                  <span className="text-slate-500 font-mono">{timeStr}</span>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span>Actor: <strong className="text-slate-300">{item.actor}</strong></span>
                  {item.from_status && item.to_status && (
                    <span>
                      • Transition: <span className="text-amber-400 font-mono">{item.from_status}</span> → <span className="text-emerald-400 font-mono">{item.to_status}</span>
                    </span>
                  )}
                </div>

                {item.reason && (
                  <p className="text-xs text-slate-300 pt-0.5 leading-relaxed">
                    {item.reason}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
