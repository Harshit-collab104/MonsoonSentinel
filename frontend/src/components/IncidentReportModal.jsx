import React, { useState } from 'react';
import { X, Send, AlertTriangle, Camera } from 'lucide-react';

const WARD_OPTIONS = [
  { id: 'WARD-BLR-01', name: 'Bengaluru - Koramangala 80ft Road & Ejipura Outfall', lat: 12.9345, lon: 77.6265 },
  { id: 'WARD-BLR-02', name: 'Bengaluru - Silk Board Junction & Madiwala Basin', lat: 12.9172, lon: 77.6228 },
  { id: 'WARD-BLR-03', name: 'Bengaluru - Bellandur Lake Spillway & Eco-Space Sluice', lat: 12.9260, lon: 77.6762 },
  { id: 'WARD-BLR-04', name: 'Bengaluru - Hebbal Flyover SWD & Nagavara Feeder', lat: 13.0358, lon: 77.5970 },
  { id: 'WARD-BOM-01', name: 'Mumbai - Hindmata Cinema & Dadar TT Pumping Station', lat: 19.0178, lon: 72.8478 },
  { id: 'WARD-BOM-02', name: 'Mumbai - Milan Subway & Santacruz West SWD', lat: 19.0833, lon: 72.8417 },
  { id: 'WARD-BOM-03', name: 'Mumbai - Kurla Mithi River Outfall & Kranti Nagar', lat: 19.0688, lon: 72.8710 },
  { id: 'WARD-DEL-01', name: 'Delhi - Minto Bridge Railway Underpass Basin', lat: 28.6358, lon: 77.2255 },
  { id: 'WARD-DEL-02', name: 'Delhi - ITO Ring Road & Yamuna Barrage Gate 12', lat: 28.6289, lon: 77.2483 },
  { id: 'WARD-CHE-01', name: 'Chennai - Velachery 100ft Road & Lake Canal', lat: 12.9792, lon: 80.2185 },
];

export default function IncidentReportModal({ isOpen, onClose, onSubmitSuccess }) {
  const [formData, setFormData] = useState({
    reporter_name: '',
    reporter_phone: '',
    ward_id: 'WARD-BLR-01',
    ward_name: 'Bengaluru - Koramangala 80ft Road & Ejipura Outfall',
    latitude: 12.9345,
    longitude: 77.6265,
    drain_blockage_level: 'COMPLETE',
    water_depth_cm: 30,
    description: '',
    landmark: '',
    image_url: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80',
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleWardChange = (e) => {
    const wardId = e.target.value;
    const selected = WARD_OPTIONS.find((w) => w.id === wardId);
    if (selected) {
      setFormData((prev) => ({
        ...prev,
        ward_id: selected.id,
        ward_name: selected.name,
        latitude: selected.lat,
        longitude: selected.lon,
      }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const objectUrl = URL.createObjectURL(file);
      setFilePreview(objectUrl);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await onSubmitSuccess({
        ...formData,
        water_depth_cm: parseFloat(formData.water_depth_cm) || 0,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
      }, selectedFile);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit waterlogging report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs select-text">
      <div className="bg-[#121214] border border-[#27272A] w-full max-w-lg rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-5 py-3.5 border-b border-[#27272A] flex items-center justify-between bg-[#121214]">
          <div>
            <h2 className="text-sm font-semibold text-white">Report Waterlogging Incident</h2>
            <p className="text-xs text-[#71717A]">Submit citizen telemetry or field engineer observation</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#71717A] hover:text-white transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-5 overflow-y-auto space-y-4 text-xs bg-[#121214]">
          {error && (
            <div className="p-3 bg-[#18181B] border border-red-900/50 text-red-400 rounded text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Reporter Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Reporter Name *</label>
              <input
                type="text"
                required
                value={formData.reporter_name}
                onChange={(e) => setFormData({ ...formData, reporter_name: e.target.value })}
                placeholder="e.g. Ananya Sen"
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-[#FAFAFA] placeholder-[#71717A] focus:border-[#3F3F46] outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Contact Phone</label>
              <input
                type="text"
                value={formData.reporter_phone}
                onChange={(e) => setFormData({ ...formData, reporter_phone: e.target.value })}
                placeholder="+91 98765 43210"
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-[#FAFAFA] placeholder-[#71717A] focus:border-[#3F3F46] outline-none"
              />
            </div>
          </div>

          {/* Ward & Location Preset */}
          <div>
            <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Municipal Ward Sector *</label>
            <select
              value={formData.ward_id}
              onChange={handleWardChange}
              className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-[#FAFAFA] focus:border-[#3F3F46] outline-none"
            >
              {WARD_OPTIONS.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>

          {/* Blockage Severity & Water Depth */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Drain Blockage Level *</label>
              <select
                value={formData.drain_blockage_level}
                onChange={(e) => setFormData({ ...formData, drain_blockage_level: e.target.value })}
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-[#FAFAFA] focus:border-[#3F3F46] outline-none"
              >
                <option value="CLEAR">Clear (0% - Free flow)</option>
                <option value="PARTIAL">Partial (~50% Silt & debris)</option>
                <option value="SEVERE">Severe (~80% Clogged intake)</option>
                <option value="COMPLETE">Complete (100% Total blockage)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Water Depth (cm)</label>
              <input
                type="number"
                min="0"
                max="250"
                value={formData.water_depth_cm}
                onChange={(e) => setFormData({ ...formData, water_depth_cm: e.target.value })}
                className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-[#FAFAFA] focus:border-[#3F3F46] outline-none"
              />
            </div>
          </div>

          {/* Landmark */}
          <div>
            <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Landmark / Corridor</label>
            <input
              type="text"
              value={formData.landmark}
              onChange={(e) => setFormData({ ...formData, landmark: e.target.value })}
              placeholder="e.g. Under Metro Pillar 142"
              className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-[#FAFAFA] placeholder-[#71717A] focus:border-[#3F3F46] outline-none"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-[#A1A1AA] mb-1">Incident Details *</label>
            <textarea
              required
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe pooling perimeter, vehicle stalls, surface debris..."
              className="w-full bg-[#18181B] border border-[#27272A] rounded p-2.5 text-xs text-[#FAFAFA] placeholder-[#71717A] focus:border-[#3F3F46] outline-none"
            />
          </div>

          {/* Photo Evidence (File upload or URL) */}
          <div className="space-y-2">
            <label className="block text-xs font-medium text-[#A1A1AA] flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Camera className="w-3.5 h-3.5 text-emerald-400" />
                <span>Evidence Photo (Local Upload or URL)</span>
              </span>
              <span className="text-[11px] text-[#71717A]">PNG, JPG, WebP</span>
            </label>

            {/* Local File Selector */}
            <div className="flex items-center gap-2">
              <label className="flex-1 cursor-pointer flex items-center justify-center gap-2 h-9 px-3 bg-[#18181B] hover:bg-[#27272A] border border-dashed border-[#3F3F46] rounded text-xs text-[#FAFAFA] transition">
                <Camera className="w-4 h-4 text-emerald-400" />
                <span className="truncate">
                  {selectedFile ? selectedFile.name : 'Choose photo from computer...'}
                </span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              {selectedFile && (
                <button
                  type="button"
                  onClick={() => { setSelectedFile(null); setFilePreview(null); }}
                  className="h-9 px-2.5 text-xs text-zinc-400 hover:text-white bg-[#18181B] border border-[#27272A] rounded cursor-pointer"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Preview if file chosen */}
            {filePreview && (
              <div className="relative rounded overflow-hidden border border-[#27272A] max-h-36 bg-black flex items-center justify-center">
                <img
                  src={filePreview}
                  alt="Evidence preview"
                  className="w-full h-36 object-cover"
                />
                <span className="absolute bottom-1 right-2 bg-black/70 px-1.5 py-0.5 rounded text-[10px] text-emerald-400 font-mono">
                  Ready to upload to S3
                </span>
              </div>
            )}

            {/* Fallback URL input */}
            {!selectedFile && (
              <div>
                <input
                  type="text"
                  value={formData.image_url}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  placeholder="Or enter image URL: https://..."
                  className="w-full h-8 bg-[#18181B] border border-[#27272A] rounded px-3 text-xs text-[#FAFAFA] placeholder-[#71717A] focus:border-[#3F3F46] outline-none"
                />
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-[#27272A] flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="h-8 px-3.5 bg-[#18181B] hover:bg-[#27272A] text-[#A1A1AA] hover:text-white border border-[#27272A] text-xs font-medium rounded transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="h-8 px-4 bg-[#10B981] hover:bg-[#059669] text-zinc-950 text-xs font-medium rounded transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>{loading ? 'Submitting...' : 'Submit Report'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

