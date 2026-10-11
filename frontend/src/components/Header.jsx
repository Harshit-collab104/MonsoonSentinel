import React from 'react';
import { Plus, Terminal, Map, ShieldCheck } from 'lucide-react';

export default function Header({ activeTab, onTabChange, pendingCount, onOpenReportModal }) {
  return (
    <header className="h-12 border-b border-[#27272A] px-4 flex items-center justify-between text-sm select-none z-30 shrink-0 bg-[#09090B]">
      {/* App Title & Subtle Indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 font-medium text-white tracking-tight">
          <span className="w-2 h-2 rounded-full bg-[#10B981] inline-block" />
          <span className="text-sm font-semibold">Monsoon Sentinel</span>
        </div>
        <span className="text-xs text-[#71717A] hidden md:inline font-mono">
          / flood dispatch v2
        </span>
      </div>

      {/* Central View Switcher (Tabs) */}
      <nav className="flex items-center bg-[#18181B] p-0.5 rounded-md border border-[#27272A]">
        <button
          onClick={() => onTabChange('console')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
            activeTab === 'console'
              ? 'bg-[#27272A] text-white shadow-xs'
              : 'text-[#A1A1AA] hover:text-white'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Console</span>
        </button>

        <button
          onClick={() => onTabChange('map')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
            activeTab === 'map'
              ? 'bg-[#27272A] text-white shadow-xs'
              : 'text-[#A1A1AA] hover:text-white'
          }`}
        >
          <Map className="w-3.5 h-3.5" />
          <span>GIS Map</span>
        </button>

        <button
          onClick={() => onTabChange('queue')}
          className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition cursor-pointer ${
            activeTab === 'queue'
              ? 'bg-[#27272A] text-white shadow-xs'
              : 'text-[#A1A1AA] hover:text-white'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Supervisor Queue</span>
          {pendingCount > 0 && (
            <span className="ml-0.5 px-1.5 py-0.2 bg-[#27272A] text-[#FAFAFA] text-[10px] rounded-full font-mono border border-[#3F3F46]">
              {pendingCount}
            </span>
          )}
        </button>
      </nav>

      {/* Single Refined Primary Action */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenReportModal}
          className="h-7 px-3 bg-[#10B981] hover:bg-[#059669] text-zinc-950 font-medium text-xs rounded transition flex items-center gap-1.5 cursor-pointer shadow-xs"
        >
          <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>New Incident</span>
        </button>
      </div>
    </header>
  );
}


