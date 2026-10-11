import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Layers, Compass } from 'lucide-react';

// Real Indian Municipal Drainage Corridors & SWD (Storm Water Drains)
const INDIAN_DRAINAGE_NETWORKS = {
  // Bengaluru Major Valleys & Primary SWD
  bengaluru: [
    // Koramangala-Challaghatta Valley Primary SWD
    [
      [12.9750, 77.5850],
      [12.9550, 77.6050],
      [12.9345, 77.6265],
      [12.9260, 77.6762],
      [12.9430, 77.7390]
    ],
    // Silk Board to Madiwala Lake Outfall
    [
      [12.9250, 77.6150],
      [12.9172, 77.6228],
      [12.9116, 77.6436],
      [12.9260, 77.6762]
    ],
    // Hebbal Valley Feeder Line
    [
      [13.0450, 77.5850],
      [13.0358, 77.5970],
      [13.0150, 77.6200],
      [12.9926, 77.7019]
    ]
  ],
  // Mumbai Mithi River & Key Subways
  mumbai: [
    // Mithi River to Mahim Creek Outfall
    [
      [19.1250, 72.8900],
      [19.0950, 72.8800],
      [19.0688, 72.8710],
      [19.0550, 72.8550],
      [19.0400, 72.8380]
    ],
    // Hindmata to Dadar Sea Outfall
    [
      [19.0178, 72.8478],
      [19.0220, 72.8400],
      [19.0260, 72.8320]
    ],
    // Milan Subway to Arabian Sea Drain
    [
      [19.0833, 72.8417],
      [19.0850, 72.8300],
      [19.0870, 72.8220]
    ]
  ],
  // Delhi Najafgarh & Yamuna Sluices
  delhi: [
    // Minto Bridge to Yamuna Basin
    [
      [28.6358, 77.2255],
      [28.6320, 77.2350],
      [28.6289, 77.2483]
    ],
    // Barapullah Drain to Yamuna
    [
      [28.5800, 77.2200],
      [28.5850, 77.2450],
      [28.5900, 77.2650]
    ]
  ],
  // Chennai Buckingham Canal & Adyar Outfall
  chennai: [
    // Velachery to Buckingham Canal & Sea
    [
      [12.9792, 80.2185],
      [12.9850, 80.2350],
      [12.9900, 80.2550]
    ],
    // Mambalam Canal / Adyar River
    [
      [13.0418, 80.2337],
      [13.0250, 80.2400],
      [13.0100, 80.2600]
    ]
  ]
};

// Strategic Indian Metro Focus Regions
const REGIONS = [
  { id: 'INDIA', name: 'All India (National)', coords: [21.5937, 78.9629], zoom: 5 },
  { id: 'BLR', name: 'Bengaluru (BBMP)', coords: [12.9550, 77.6350], zoom: 12 },
  { id: 'BOM', name: 'Mumbai (BMC)', coords: [19.0600, 72.8550], zoom: 12 },
  { id: 'DEL', name: 'Delhi NCR (I&FC)', coords: [28.6400, 77.2200], zoom: 12 },
  { id: 'CHE', name: 'Chennai (GCC)', coords: [13.0200, 80.2300], zoom: 12 },
];

export default function IncidentMap({ incidents = [], selectedIncident, onSelectIncident }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const channelsLayerRef = useRef(null);
  const baseTilesLayerRef = useRef(null);

  const [currentRegion, setCurrentRegion] = useState('INDIA');
  const [selectedWard, setSelectedWard] = useState('ALL');
  const [showChannels, setShowChannels] = useState(true);
  const [mapStyle, setMapStyle] = useState('dark');

  // Collect distinct ward sectors from incidents
  const wardList = [
    { id: 'ALL', name: 'All Sectors' },
    ...Array.from(new Set(incidents.map((i) => i.report.ward_id))).map((wId) => {
      const match = incidents.find((i) => i.report.ward_id === wId);
      return { id: wId, name: match ? match.report.ward_name : wId };
    }),
  ];

  const filteredIncidents = incidents.filter(
    (inc) => selectedWard === 'ALL' || inc.report.ward_id === selectedWard
  );

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center on India
    const map = L.map(mapContainerRef.current, {
      center: [21.5937, 78.9629],
      zoom: 5,
      zoomControl: true,
      attributionControl: false,
      minZoom: 4,
      maxZoom: 18,
    });

    // Create Layer Groups
    const baseTilesLayer = L.layerGroup().addTo(map);
    const channelsLayer = L.layerGroup().addTo(map);
    const markersLayer = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;
    baseTilesLayerRef.current = baseTilesLayer;
    channelsLayerRef.current = channelsLayer;
    markersLayerRef.current = markersLayer;

    // Leaflet map container resize handler
    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize();
    });
    resizeObserver.observe(mapContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Base Map Tiles (Zero API Key, No Watermark)
  useEffect(() => {
    if (!baseTilesLayerRef.current) return;
    baseTilesLayerRef.current.clearLayers();

    if (mapStyle === 'satellite') {
      // ESRI High-Resolution World Imagery + Reference Boundaries
      const satLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19 }
      );
      const labelsLayer = L.tileLayer(
        'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 19 }
      );
      satLayer.addTo(baseTilesLayerRef.current);
      labelsLayer.addTo(baseTilesLayerRef.current);
    } else if (mapStyle === 'streets') {
      // OpenStreetMap Standard
      const osmLayer = L.tileLayer(
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        { maxZoom: 19 }
      );
      osmLayer.addTo(baseTilesLayerRef.current);
    } else {
      // Tactical Dark: ESRI Dark Gray Canvas (Completely Free, No API Key, No Watermark)
      const darkBase = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 18 }
      );
      const darkRef = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 18 }
      );
      darkBase.addTo(baseTilesLayerRef.current);
      darkRef.addTo(baseTilesLayerRef.current);
    }
  }, [mapStyle]);

  // Update Drainage Network Overlays
  useEffect(() => {
    if (!channelsLayerRef.current) return;
    channelsLayerRef.current.clearLayers();

    if (!showChannels) return;

    Object.values(INDIAN_DRAINAGE_NETWORKS).forEach((network) => {
      network.forEach((line) => {
        L.polyline(line, {
          color: '#3B82F6',
          weight: 2.5,
          opacity: 0.6,
          dashArray: '5, 8',
        }).addTo(channelsLayerRef.current);
      });
    });
  }, [showChannels]);

  // Update Incident Markers
  useEffect(() => {
    if (!markersLayerRef.current || !mapInstanceRef.current) return;
    markersLayerRef.current.clearLayers();

    filteredIncidents.forEach((incident) => {
      const lat = incident.report.latitude;
      const lon = incident.report.longitude;
      if (!lat || !lon) return;

      const isSelected = selectedIncident?.id === incident.id;
      const status = incident.status;
      const sev = incident.risk_assessment?.severity || 'LOW';
      const depth = incident.report.water_depth_cm || 0;

      // Color scheme based on status and severity
      let badgeBg = '#18181B';
      let borderCol = '#3F3F46';
      let textColor = '#E4E4E7';
      let pulseRing = '';

      if (status === 'VERIFIED' || status === 'RESOLVED') {
        // Green for cleared/verified incidents
        badgeBg = '#064E3B';
        borderCol = '#10B981';
        textColor = '#D1FAE5';
      } else if (sev === 'CRITICAL') {
        badgeBg = '#450A0A';
        borderCol = '#EF4444';
        textColor = '#FEF2F2';
        pulseRing = `<span class="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span>
                     <span class="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500"></span>`;
      } else if (sev === 'HIGH') {
        badgeBg = '#431407';
        borderCol = '#F97316';
        textColor = '#FFF7ED';
      } else if (sev === 'MEDIUM') {
        badgeBg = '#27272A';
        borderCol = '#F59E0B';
        textColor = '#FAFAFA';
      }

      const ringClass = isSelected ? 'border-2 border-white scale-110 shadow-[0_0_12px_rgba(255,255,255,0.4)]' : 'border';

      // Custom DivIcon HTML
      const isCleared = status === 'VERIFIED' || status === 'RESOLVED';
      const labelText = isCleared ? 'CLEARED' : (depth > 0 ? `${depth}cm` : incident.id.slice(-4));

      const iconHtml = `
        <div style="background-color: ${badgeBg}; border-color: ${borderCol}; color: ${textColor};"
             class="relative px-2 py-1 rounded text-[11px] font-mono font-medium shadow-md flex items-center gap-1.5 whitespace-nowrap transition cursor-pointer select-none ${ringClass}">
          ${pulseRing}
          <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${
              isCleared
                ? 'M5 13l4 4L19 7'
                : 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z'
            }" />
          </svg>
          <span>${labelText}</span>
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-incident-marker',
        html: iconHtml,
        iconSize: [60, 26],
        iconAnchor: [30, 13],
      });

      const marker = L.marker([lat, lon], { icon: customIcon }).addTo(markersLayerRef.current);

      // Bind Tooltip
      const tooltipContent = `
        <div class="bg-[#18181B] border border-[#3F3F46] rounded p-2 text-xs text-white shadow-xl min-w-[200px]">
          <div class="flex items-center justify-between pb-1 mb-1 border-b border-[#27272A] font-mono">
            <span class="text-zinc-400 font-bold">${incident.id}</span>
            <span class="px-1.5 py-0.2 rounded text-[10px] font-semibold ${
              sev === 'CRITICAL' ? 'bg-red-950 text-red-300' : 'bg-zinc-800 text-zinc-300'
            }">${incident.status}</span>
          </div>
          <div class="font-medium text-white text-xs mb-1">${incident.report.ward_name}</div>
          <div class="text-[11px] text-zinc-400 line-clamp-2">${incident.report.description}</div>
          <div class="mt-1 pt-1 border-t border-[#27272A] flex justify-between text-[11px]">
            <span class="text-zinc-500">Water Depth: <strong class="text-zinc-200">${depth} cm</strong></span>
            <span class="text-zinc-500">Risk: <strong class="text-amber-400">${incident.risk_assessment?.risk_score || 'N/A'}/100</strong></span>
          </div>
        </div>
      `;

      marker.bindTooltip(tooltipContent, {
        direction: 'top',
        offset: [0, -12],
        opacity: 0.98,
        className: 'incident-leaflet-tooltip',
      });

      marker.on('click', () => {
        onSelectIncident?.(incident);
      });
    });
  }, [filteredIncidents, selectedIncident, onSelectIncident]);

  // Pan to selected incident when it changes
  useEffect(() => {
    if (!selectedIncident || !mapInstanceRef.current) return;
    const lat = selectedIncident.report.latitude;
    const lon = selectedIncident.report.longitude;
    if (lat && lon) {
      mapInstanceRef.current.flyTo([lat, lon], 14, { duration: 1.2 });
    }
  }, [selectedIncident]);

  // Handle Region Quick-Jump
  const handleRegionChange = (reg) => {
    setCurrentRegion(reg.id);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(reg.coords, reg.zoom, { duration: 1.2 });
    }
  };

  return (
    <div className="w-full h-full bg-[#09090B] overflow-hidden flex flex-col select-none relative">
      {/* Top Map Tactical Control Bar */}
      <div className="h-11 px-4 border-b border-[#27272A] flex items-center justify-between text-xs shrink-0 bg-[#09090B] z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-medium text-[#FAFAFA]">
            <Compass className="w-4 h-4 text-emerald-400 animate-spin-slow" />
            <span>India Municipal GIS Radar</span>
          </div>
          <span className="text-[#71717A] hidden sm:inline">
            ({filteredIncidents.length} active locations)
          </span>

          {/* Quick Region Switcher Buttons */}
          <div className="hidden lg:flex items-center gap-1 border-l border-[#27272A] pl-3 ml-1">
            {REGIONS.map((r) => (
              <button
                key={r.id}
                onClick={() => handleRegionChange(r)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition cursor-pointer ${
                  currentRegion === r.id
                    ? 'bg-[#27272A] text-white border border-[#3F3F46]'
                    : 'text-[#71717A] hover:text-[#E4E4E7]'
                }`}
              >
                {r.name}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Mobile Region Dropdown */}
          <select
            value={currentRegion}
            onChange={(e) => {
              const reg = REGIONS.find((r) => r.id === e.target.value);
              if (reg) handleRegionChange(reg);
            }}
            className="lg:hidden h-7 bg-[#18181B] text-[#E4E4E7] text-xs px-2 rounded border border-[#27272A] outline-none"
          >
            {REGIONS.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>

          {/* Basemap Style Selector (Keyless, Watermark-free) */}
          <select
            value={mapStyle}
            onChange={(e) => setMapStyle(e.target.value)}
            className="h-7 bg-[#18181B] text-[#E4E4E7] text-xs px-2 rounded border border-[#27272A] outline-none focus:border-[#3F3F46]"
            title="Basemap View"
          >
            <option value="dark">Tactical Dark</option>
            <option value="satellite">Satellite</option>
            <option value="streets">OpenStreetMap</option>
          </select>

          {/* Ward Sector Selector */}
          <select
            value={selectedWard}
            onChange={(e) => setSelectedWard(e.target.value)}
            className="h-7 bg-[#18181B] text-[#E4E4E7] text-xs px-2.5 rounded border border-[#27272A] outline-none focus:border-[#3F3F46] max-w-[180px] truncate"
          >
            {wardList.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>

          {/* Toggle Drainage Network Vectors */}
          <button
            onClick={() => setShowChannels(!showChannels)}
            className={`h-7 px-2.5 text-xs font-medium rounded border transition flex items-center gap-1.5 cursor-pointer ${
              showChannels
                ? 'bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]'
                : 'bg-[#18181B] border-[#27272A] text-[#71717A] hover:text-[#FAFAFA]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">SWD Network</span>
          </button>
        </div>
      </div>

      {/* Map Canvas */}
      <div className="relative flex-1 bg-[#09090B] overflow-hidden">
        <div ref={mapContainerRef} className="w-full h-full z-0" />

        {/* Tactical Legend Overlay */}
        <div className="absolute bottom-3 left-3 bg-[#09090B]/90 backdrop-blur-sm border border-[#27272A] rounded p-2.5 text-[11px] text-[#A1A1AA] z-10 pointer-events-auto space-y-1.5 shadow-lg">
          <div className="text-zinc-200 font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
            GIS Telemetry Radar (India)
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm bg-red-950 border border-red-500 inline-block"></span>
            <span>Critical Severity (Flooded &gt; 40cm)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#431407] border border-orange-500 inline-block"></span>
            <span>High Severity (Waterlogging 20-40cm)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-4 h-0.5 border-t-2 border-dashed border-blue-500 inline-block"></span>
            <span>Municipal SWD Drainage Network</span>
          </div>
        </div>
      </div>
    </div>
  );
}
