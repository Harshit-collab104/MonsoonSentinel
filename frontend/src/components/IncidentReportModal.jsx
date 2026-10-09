import React, { useState } from 'react';
import { X, Send, AlertTriangle, MapPin, Droplets, Camera } from 'lucide-react';

const WARD_OPTIONS = [
  { id: 'WARD-12', name: 'Central Metro & Commercial Hub', lat: 12.9716, lon: 77.5946 },
  { id: 'WARD-07', name: 'South Lakeside & Riverfront Drainage Basin', lat: 12.9352, lon: 77.6245 },
  { id: 'WARD-04', name: 'North Industrial Estate & Culvert Zone', lat: 13.0358, lon: 77.5970 },
  { id: 'WARD-19', name: 'Eastern Hills Residential Heights', lat: 12.9850, lon: 77.6680 },
];

export default function IncidentReportModal({ isOpen, onClose, onSubmitSuccess }) {
  const [formData, setFormData] = useState({
    reporter_name: '',
    reporter_phone: '',
    ward_id: 'WARD-12',
    ward_name: 'Central Metro & Commercial Hub',
    latitude: 12.9716,
    longitude: 77.5946,
    drain_blockage_level: 'COMPLETE',
    water_depth_cm: 30,
    description: '',
    landmark: '',
    image_url: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80',
  });

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
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to submit waterlogging report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Droplets className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Report Waterlogging Incident</h2>
              <p className="text-xs text-slate-400">Step 1: Citizen Submission & Intake Triage</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-5 overflow-y-auto space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Reporter Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Your Name *</label>
              <input
                type="text"
                required
                value={formData.reporter_name}
                onChange={(e) => setFormData({ ...formData, reporter_name: e.target.value })}
                placeholder="e.g. Ananya Sen"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Phone Number</label>
              <input
                type="text"
                value={formData.reporter_phone}
                onChange={(e) => setFormData({ ...formData, reporter_phone: e.target.value })}
                placeholder="+91-98765-43210"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 outline-none"
              />
            </div>
          </div>

          {/* Ward & Location Preset */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Municipal Ward Zone *</label>
            <select
              value={formData.ward_id}
              onChange={handleWardChange}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:border-blue-500 outline-none"
            >
              {WARD_OPTIONS.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.id} - {w.name}
                </option>
              ))}
            </select>
          </div>

          {/* Coordinates & Landmark */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                required
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                required
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:border-blue-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Landmark / Specific Location</label>
            <input
              type="text"
              value={formData.landmark}
              onChange={(e) => setFormData({ ...formData, landmark: e.target.value })}
              placeholder="e.g. Near Metro Underpass Pillar 24"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Blockage Severity & Water Depth */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Drain Blockage Severity *</label>
              <select
                value={formData.drain_blockage_level}
                onChange={(e) => setFormData({ ...formData, drain_blockage_level: e.target.value })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:border-blue-500 outline-none"
              >
                <option value="CLEAR">CLEAR (No physical blockage)</option>
                <option value="PARTIAL">PARTIAL (Silt / partial leaves)</option>
                <option value="SEVERE">SEVERE (Heavy silt & debris)</option>
                <option value="COMPLETE">COMPLETE (100% Clogged / Impassable)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Water Depth (cm)</label>
              <input
                type="number"
                min="0"
                max="200"
                value={formData.water_depth_cm}
                onChange={(e) => setFormData({ ...formData, water_depth_cm: e.target.value })}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:border-blue-500 outline-none"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Incident Description *</label>
            <textarea
              required
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the pooling extent, pedestrian/vehicle impact, and trapped debris..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Photo Evidence URL */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center gap-1.5">
              <Camera className="w-3.5 h-3.5 text-slate-400" />
              <span>Evidence Photo URL (Optional)</span>
            </label>
            <input
              type="url"
              value={formData.image_url}
              onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
              placeholder="https://..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 outline-none"
            />
          </div>

          {/* Submit Action */}
          <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-blue-900/30 transition disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{loading ? 'Submitting...' : 'Submit Incident Report'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
