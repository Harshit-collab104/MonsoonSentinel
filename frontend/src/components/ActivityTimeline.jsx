import React from 'react';
import { History, User, Cpu, ShieldCheck, Wrench, Shield } from 'lucide-react';

export default function ActivityTimeline({ auditHistory }) {
  if (!auditHistory || auditHistory.length === 0) {
    return (
      <div className="p-4 text-center text-xs text-[#71717A]">
        No audit events logged yet.
      </div>
    );
  }

  const getActorIcon = (actor) => {
    if (actor.includes('citizen')) return <User className="w-3.5 h-3.5 text-[#A1A1AA]" />;
    if (actor.includes('risk_engine')) return <Cpu className="w-3.5 h-3.5 text-[#A1A1AA]" />;
    if (actor.includes('strands_agent')) return <Cpu className="w-3.5 h-3.5 text-[#10B981]" />;
    if (actor.includes('supervisor')) return <Shield className="w-3.5 h-3.5 text-[#A1A1AA]" />;
    if (actor.includes('crew')) return <Wrench className="w-3.5 h-3.5 text-[#A1A1AA]" />;
    if (actor.includes('verification')) return <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" />;
    return <History className="w-3.5 h-3.5 text-[#71717A]" />;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <History className="w-4 h-4 text-[#A1A1AA]" />
        <h4 className="text-xs font-semibold text-white uppercase tracking-wider">
          Audit Trail ({auditHistory.length} events)
        </h4>
      </div>

      <div className="relative pl-5 space-y-3 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[1px] before:bg-[#27272A]">
        {auditHistory.map((item, index) => {
          const date = new Date(item.timestamp);
          const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

          return (
            <div key={index} className="relative group">
              {/* Timeline Indicator Dot */}
              <div className="absolute -left-5 top-1 w-4 h-4 rounded-full bg-[#18181B] border border-[#27272A] flex items-center justify-center">
                {getActorIcon(item.actor)}
              </div>

              {/* Event Card */}
              <div className="bg-[#121214] border border-[#27272A] rounded p-2.5 space-y-1 text-left text-xs">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-medium text-white">
                    {item.action}
                  </span>
                  <span className="text-[#71717A] text-[11px] font-mono">{timeStr}</span>
                </div>

                <div className="flex items-center gap-2 text-xs text-[#71717A]">
                  <span>Actor: <strong className="text-[#A1A1AA] font-normal">{item.actor}</strong></span>
                  {item.from_status && item.to_status && (
                    <span>
                      • <span className="text-[#A1A1AA]">{item.from_status}</span> → <span className="text-white">{item.to_status}</span>
                    </span>
                  )}
                </div>

                {item.reason && (
                  <p className="text-xs text-[#A1A1AA] pt-0.5 leading-relaxed">
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

