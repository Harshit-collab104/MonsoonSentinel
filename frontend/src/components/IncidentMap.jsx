import React, { useState } from 'react';
import { MapPin, Navigation, Eye, AlertTriangle, Layers, Droplets } from 'lucide-react';

const WARDS = [
  { id: 'ALL', name: 'All Wards' },
  { id: 'WARD-12', name: 'Ward 12 (Central Metro)' },
  { id: 'WARD-07', name: 'Ward 7 (South Lakeside)' },
  { id: 'WARD-04', name: 'Ward 4 (North Industrial)' },
  { id: 'WARD-19', name: 'Ward 19 (Eastern Hills)' },
];

export default function IncidentMap({ incidents, selectedIncident, onSelectIncident }) {
  const [selectedWard, setSelectedWard] = useState('ALL');
  const [showChannels, setShowChannels] = useState(true);

  const filteredIncidents = incidents.filter(
    (inc) => selectedWard === 'ALL' || inc.report.ward_id === selectedWard
  );

  // Coordinate projection into relative 0-100% SVG box for urban grid
  // Bangalore urban center bounding box: Lat ~12.92 to ~13.05, Lon ~77.56 to ~77.68
  const projectCoords = (lat, lon) => {
    const minLat = 12.92;
    const maxLat = 13.05;
    const minLon = 77.56;
    const maxLon = 77.68;

    const x = Math.min(92, Math.max(8, ((lon - minLon) / (maxLon - minLon)) * 100));
    // Invert Y for latitude since SVG y=0 is top
    const y = Math.min(92, Math.max(8, 100 - ((lat - minLat) / (maxLat - minLat)) * 100));
    return { x, y };
  };

  const getMarkerColor = (incident) => {
    const sev = incident.risk_assessment?.severity || 'LOW';
    if (sev === 'CRITICAL') return 'bg-red-500 border-red-300 text-white shadow-red-500/50';
    if (sev === 'HIGH') return 'bg-orange-500 border-orange-300 text-white shadow-orange-500/50';
    if (sev === 'MEDIUM') return 'bg-yellow-500 border-yellow-200 text-slate-900 shadow-yellow-500/50';
    return 'bg-emerald-500 border-emerald-300 text-white shadow-emerald-500/50';
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-lg">
      {/* Top Map Controls */}
      <div className="p-3 bg-slate-900/90 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            Municipal Ward & Hydrological Grid
          </span>
          <span className="text-[11px] text-slate-400">
            ({filteredIncidents.length} active markers)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Ward Selector */}
          <select
            value={selectedWard}
            onChange={(e) => setSelectedWard(e.target.value)}
            className="bg-slate-800 text-slate-200 text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 outline-none focus:border-blue-500"
          >
            {WARDS.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>

          {/* Toggle Drainage Overlay */}
          <button
            onClick={() => setShowChannels(!showChannels)}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 cursor-pointer ${
              showChannels
                ? 'bg-blue-600/20 border-blue-500/40 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Drainage Corridors</span>
          </button>
        </div>
      </div>

      {/* Map Canvas / Grid Representation */}
      <div className="relative w-full h-[360px] md:h-[420px] bg-slate-950 overflow-hidden select-none">
        {/* Subtle Map Grid Lines */}
        <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-70" />

        {/* Drainage Channels SVG Layer */}
        {showChannels && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-45">
            {/* Primary Stormwater Outfall Arteries */}
            <path
              d="M 20 20 Q 35 120 50 210 T 80 380"
              fill="none"
              stroke="#0284c7"
              strokeWidth="4"
              strokeDasharray="6 3"
            />
            <path
              d="M 85 40 Q 60 180 50 210 T 30 360"
              fill="none"
              stroke="#0284c7"
              strokeWidth="3.5"
            />
            <path
              d="M 10 200 L 90 220"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeDasharray="4 2"
            />
          </svg>
        )}

        {/* Municipal Ward Boundary Cards / Labels */}
        <div className="absolute top-4 left-4 p-2 rounded-lg bg-slate-900/80 border border-slate-800 backdrop-blur pointer-events-none">
          <div className="text-[10px] font-bold text-slate-400">SECTOR NORTH</div>
          <div className="text-xs font-semibold text-slate-200">Ward 04: Industrial Culvert</div>
        </div>
        <div className="absolute top-1/3 left-1/3 p-2 rounded-lg bg-slate-900/80 border border-slate-800 backdrop-blur pointer-events-none">
          <div className="text-[10px] font-bold text-blue-400">METRO UNDERPASS HUB</div>
          <div className="text-xs font-semibold text-slate-200">Ward 12: Central Hub</div>
        </div>
        <div className="absolute bottom-4 left-6 p-2 rounded-lg bg-slate-900/80 border border-slate-800 backdrop-blur pointer-events-none">
          <div className="text-[10px] font-bold text-cyan-400">DRAINAGE BASIN</div>
          <div className="text-xs font-semibold text-slate-200">Ward 07: South Lakeside</div>
        </div>
        <div className="absolute top-12 right-6 p-2 rounded-lg bg-slate-900/80 border border-slate-800 backdrop-blur pointer-events-none">
          <div className="text-[10px] font-bold text-slate-400">ELEVATED SECTOR</div>
          <div className="text-xs font-semibold text-slate-200">Ward 19: Eastern Hills</div>
        </div>

        {/* Incident Interactive Markers */}
        {filteredIncidents.map((incident) => {
          const { x, y } = projectCoords(incident.report.latitude, incident.report.longitude);
          const isSelected = selectedIncident?.id === incident.id;
          const sev = incident.risk_assessment?.severity || 'LOW';
          const isCritical = sev === 'CRITICAL' || sev === 'HIGH';

          return (
            <div
              key={incident.id}
              onClick={() => onSelectIncident(incident)}
              style={{ left: `${x}%`, top: `${y}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-20"
            >
              {/* Pulsing ring for critical/high incidents */}
              {isCritical && (
                <span className="absolute -inset-2 rounded-full bg-red-500/30 animate-ping pointer-events-none" />
              )}

              {/* Pin Bubble */}
              <div
                className={`relative px-2 py-1 rounded-full border shadow-lg flex items-center gap-1 transition transform group-hover:scale-110 ${
                  getMarkerColor(incident)
                } ${isSelected ? 'ring-4 ring-blue-400 scale-110' : ''}`}
              >
                <MapPin className="w-3.5 h-3.5" />
                <span className="text-[11px] font-bold">
                  {incident.report.water_depth_cm ? `${incident.report.water_depth_cm}cm` : incident.id.slice(-4)}
                </span>
              </div>

              {/* Hover Tooltip Card */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 p-2.5 rounded-xl bg-slate-900 border border-slate-700 shadow-xl opacity-0 group-hover:opacity-100 transition pointer-events-none z-30">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-mono font-bold text-slate-200">{incident.id}</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                    {incident.status}
                  </span>
                </div>
                <div className="text-xs font-semibold text-white line-clamp-1">
                  {incident.report.ward_name}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">
                  {incident.report.description}
                </div>
                <div className="mt-1.5 pt-1.5 border-t border-slate-800 flex items-center justify-between text-[10px]">
                  <span className="text-slate-400">Risk Score:</span>
                  <span className="font-bold text-amber-400">
                    {incident.risk_assessment ? `${incident.risk_assessment.risk_score}/100` : 'Pending'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Map Legend Footer */}
      <div className="p-2.5 bg-slate-900 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-slate-300">Severity Pins:</span>
          <span className="flex items-center gap-1 text-red-400">
            <span className="w-2 h-2 rounded-full bg-red-500" /> Critical (≥75)
          </span>
          <span className="flex items-center gap-1 text-orange-400">
            <span className="w-2 h-2 rounded-full bg-orange-500" /> High (55-74)
          </span>
          <span className="flex items-center gap-1 text-yellow-400">
            <span className="w-2 h-2 rounded-full bg-yellow-500" /> Medium (35-54)
          </span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Low (&lt;35)
          </span>
        </div>
        <div className="text-slate-500">Click any marker to view analysis & dispatch response</div>
      </div>
    </div>
  );
}
