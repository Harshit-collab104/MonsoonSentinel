import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

# Preloaded municipal ward knowledge base & sensor network metadata
WARD_KNOWLEDGE_BASE = {
    "WARD-12": {
        "name": "Central Metro & Commercial Hub",
        "historical_waterlogging_frequency": "HIGH", # Chronic hotspot
        "historical_score": 85.0,
        "base_elevation_m": 14.2,
        "is_low_elevation_underpass": True,
        "has_hospital_or_transit": True,
        "drain_capacity_cusecs": 120.0,
        "drain_network_id": "DRN-C12-MAIN",
        "primary_gauge_id": "RAIN-G12"
    },
    "WARD-04": {
        "name": "North Industrial Estate & Culvert Zone",
        "historical_waterlogging_frequency": "MEDIUM",
        "historical_score": 55.0,
        "base_elevation_m": 18.5,
        "is_low_elevation_underpass": False,
        "has_hospital_or_transit": False,
        "drain_capacity_cusecs": 85.0,
        "drain_network_id": "DRN-N04-CULVERT",
        "primary_gauge_id": "RAIN-G04"
    },
    "WARD-07": {
        "name": "South Lakeside & Riverfront Drainage Basin",
        "historical_waterlogging_frequency": "HIGH",
        "historical_score": 90.0,
        "base_elevation_m": 11.0,
        "is_low_elevation_underpass": True,
        "has_hospital_or_transit": True,
        "drain_capacity_cusecs": 210.0,
        "drain_network_id": "DRN-S07-BASIN",
        "primary_gauge_id": "RAIN-G07"
    },
    "WARD-19": {
        "name": "Eastern Hills Residential Heights",
        "historical_waterlogging_frequency": "LOW",
        "historical_score": 15.0,
        "base_elevation_m": 35.0,
        "is_low_elevation_underpass": False,
        "has_hospital_or_transit": False,
        "drain_capacity_cusecs": 70.0,
        "drain_network_id": "DRN-E19-SLOPE",
        "primary_gauge_id": "RAIN-G19"
    }
}

# Simulated sensor feeds for rainfall intensity (mm/h)
GAUGE_TELEMETRY = {
    "RAIN-G12": {"intensity_mm_per_hr": 42.5, "status": "ONLINE", "forecast_next_2h_mm": 55.0},
    "RAIN-G04": {"intensity_mm_per_hr": 24.0, "status": "ONLINE", "forecast_next_2h_mm": 30.0},
    "RAIN-G07": {"intensity_mm_per_hr": 48.0, "status": "ONLINE", "forecast_next_2h_mm": 62.0},
    "RAIN-G19": {"intensity_mm_per_hr": 8.0, "status": "ONLINE", "forecast_next_2h_mm": 12.0},
}

class EnvironmentalDataService:
    """Provides rainfall, historical hotspot, drainage, and infrastructure data.
    Identifies missing data explicitly instead of assuming 0 or normal.
    """

    @classmethod
    def get_rainfall_forecast(cls, latitude: float, longitude: float, ward_id: Optional[str] = None) -> Dict[str, Any]:
        ward_info = WARD_KNOWLEDGE_BASE.get(ward_id or "WARD-12")
        gauge_id = ward_info.get("primary_gauge_id") if ward_info else "RAIN-G12"
        telemetry = GAUGE_TELEMETRY.get(gauge_id)

        if not telemetry or telemetry.get("status") != "ONLINE":
            return {
                "is_missing": True,
                "rainfall_intensity_mm_h": None,
                "forecast_next_2h_mm": None,
                "gauge_status": "OFFLINE",
                "notes": f"Rain gauge {gauge_id} is offline or unreachable. Rainfall data flagged as missing."
            }

        return {
            "is_missing": False,
            "rainfall_intensity_mm_h": telemetry["intensity_mm_per_hr"],
            "forecast_next_2h_mm": telemetry["forecast_next_2h_mm"],
            "gauge_status": "ONLINE",
            "gauge_id": gauge_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "notes": "Telemetry retrieved from Municipal Radar & Automated Weather Station (Simulated)"
        }

    @classmethod
    def get_historical_waterlogging(cls, ward_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        ward = WARD_KNOWLEDGE_BASE.get(ward_id)
        if not ward:
            return {
                "is_missing": True,
                "historical_score": 40.0, # Neutral baseline
                "frequency": "UNKNOWN",
                "notes": f"Ward {ward_id} not registered in municipal historical hotspot atlas."
            }

        return {
            "is_missing": False,
            "ward_name": ward["name"],
            "frequency": ward["historical_waterlogging_frequency"],
            "historical_score": ward["historical_score"],
            "is_known_hotspot": ward["historical_score"] >= 70.0,
            "notes": f"Historical flood records from 2018-2025 monsoon seasons for {ward['name']}."
        }

    @classmethod
    def get_drainage_status(cls, ward_id: str, drain_id: Optional[str] = None) -> Dict[str, Any]:
        ward = WARD_KNOWLEDGE_BASE.get(ward_id)
        if not ward:
            return {
                "is_missing": True,
                "drain_id": drain_id or "UNKNOWN",
                "capacity_cusecs": None,
                "silt_accumulation_pct": None,
                "notes": "Drainage network telemetry unavailable for this zone."
            }

        return {
            "is_missing": False,
            "drain_network_id": ward["drain_network_id"],
            "capacity_cusecs": ward["drain_capacity_cusecs"],
            "last_inspected_days_ago": 14,
            "structural_condition": "ADEQUATE" if ward["drain_capacity_cusecs"] > 100 else "CONSTRAINED",
            "notes": "Municipal stormwater master plan drainage baseline."
        }

    @classmethod
    def get_infrastructure_vulnerability(cls, ward_id: str) -> Dict[str, Any]:
        ward = WARD_KNOWLEDGE_BASE.get(ward_id)
        if not ward:
            return {
                "is_missing": True,
                "vulnerability_score": 40.0,
                "notes": "Infrastructure classification not cataloged."
            }

        vulnerability_score = 40.0
        details = []
        if ward.get("is_low_elevation_underpass"):
            vulnerability_score += 35.0
            details.append("Low elevation underpass zone")
        if ward.get("has_hospital_or_transit"):
            vulnerability_score += 25.0
            details.append("Critical hospital and transit artery")

        vulnerability_score = min(100.0, vulnerability_score)
        return {
            "is_missing": False,
            "vulnerability_score": vulnerability_score,
            "elevation_m": ward.get("base_elevation_m"),
            "critical_assets": details,
            "notes": "Evaluated against municipal emergency corridor priority list."
        }

    @classmethod
    def haversine_distance_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
