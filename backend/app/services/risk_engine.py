from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.core.enums import Severity, BlockageSeverity
from app.models.risk import RiskAssessment, RiskFactorBreakdown
from app.models.incident import Incident
from app.services.environmental import EnvironmentalDataService

class RiskEngine:
    """Deterministic, explainable Python risk calculation engine for urban waterlogging.
    Normalizes multi-source inputs, tracks missing data explicitly, and computes
    audit-ready risk scores.
    """

    # Configurable Factor Weights (Must sum to 1.0)
    WEIGHT_RAINFALL = 0.35
    WEIGHT_BLOCKAGE = 0.30
    WEIGHT_HISTORICAL = 0.15
    WEIGHT_NEARBY = 0.10
    WEIGHT_INFRASTRUCTURE = 0.10

    # Severity Thresholds
    THRESHOLD_CRITICAL = 75.0
    THRESHOLD_HIGH = 55.0
    THRESHOLD_MEDIUM = 35.0

    @classmethod
    def normalize_rainfall(cls, rainfall_mm_h: Optional[float]) -> float:
        """Normalizes rainfall intensity (mm/h) to [0, 100]."""
        if rainfall_mm_h is None:
            return 40.0 # Neutral fallback if missing
        if rainfall_mm_h <= 0.0:
            return 0.0
        elif rainfall_mm_h < 15.0:
            # Light rain: scales 10 to 35
            return 10.0 + (rainfall_mm_h / 15.0) * 25.0
        elif rainfall_mm_h <= 35.0:
            # Moderate rain: scales 35 to 70
            return 35.0 + ((rainfall_mm_h - 15.0) / 20.0) * 35.0
        else:
            # Heavy / Torrential: scales 70 to 100 (capped at 100 for >= 60 mm/h)
            excess = min(rainfall_mm_h - 35.0, 25.0)
            return min(100.0, 70.0 + (excess / 25.0) * 30.0)

    @classmethod
    def normalize_blockage(cls, level: BlockageSeverity) -> float:
        """Normalizes drain blockage severity to [0, 100]."""
        mapping = {
            BlockageSeverity.CLEAR: 0.0,
            BlockageSeverity.PARTIAL: 50.0,
            BlockageSeverity.SEVERE: 80.0,
            BlockageSeverity.COMPLETE: 100.0,
        }
        return mapping.get(level, 50.0)

    @classmethod
    def normalize_nearby_incidents(cls, nearby_count: int, max_recency_hours: float) -> float:
        """Normalizes nearby active incidents density to [0, 100]."""
        if nearby_count == 0:
            return 0.0
        # More nearby incidents in the last 2 hours sharply increase localized pooling probability
        base = min(100.0, nearby_count * 25.0)
        recency_multiplier = 1.0 if max_recency_hours <= 2.0 else 0.7
        return min(100.0, base * recency_multiplier)

    @classmethod
    def determine_severity(cls, score: float) -> Severity:
        if score >= cls.THRESHOLD_CRITICAL:
            return Severity.CRITICAL
        elif score >= cls.THRESHOLD_HIGH:
            return Severity.HIGH
        elif score >= cls.THRESHOLD_MEDIUM:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    @classmethod
    def calculate_risk(
        cls,
        incident: Incident,
        nearby_incidents: Optional[List[Incident]] = None
    ) -> RiskAssessment:
        factors: List[RiskFactorBreakdown] = []
        missing_factors: List[str] = []
        uncertainty_penalty = 0.0

        rep = incident.report

        # 1. Rainfall Forecast
        rain_data = EnvironmentalDataService.get_rainfall_forecast(
            latitude=rep.latitude,
            longitude=rep.longitude,
            ward_id=rep.ward_id
        )
        if rain_data.get("is_missing"):
            missing_factors.append("rainfall_forecast")
            uncertainty_penalty += 5.0
            rain_norm = cls.normalize_rainfall(None)
            rain_notes = f"Missing telemetry: {rain_data.get('notes')}"
        else:
            rain_val = rain_data.get("rainfall_intensity_mm_h", 0.0)
            rain_norm = cls.normalize_rainfall(rain_val)
            rain_notes = f"Gauge {rain_data.get('gauge_id')}: {rain_val} mm/h (Next 2h: {rain_data.get('forecast_next_2h_mm')} mm)"

        rain_contribution = round(rain_norm * cls.WEIGHT_RAINFALL, 2)
        factors.append(RiskFactorBreakdown(
            factor_name="Rainfall Intensity",
            raw_value=rain_data.get("rainfall_intensity_mm_h"),
            normalized_score=round(rain_norm, 2),
            weight=cls.WEIGHT_RAINFALL,
            contribution=rain_contribution,
            is_missing=rain_data.get("is_missing", False),
            notes=rain_notes
        ))

        # 2. Drain Blockage Severity
        block_norm = cls.normalize_blockage(rep.drain_blockage_level)
        block_contrib = round(block_norm * cls.WEIGHT_BLOCKAGE, 2)
        factors.append(RiskFactorBreakdown(
            factor_name="Drain Blockage Severity",
            raw_value=rep.drain_blockage_level.value,
            normalized_score=round(block_norm, 2),
            weight=cls.WEIGHT_BLOCKAGE,
            contribution=block_contrib,
            is_missing=False,
            notes=f"Reported blockage degree: {rep.drain_blockage_level.value}"
        ))

        # 3. Historical Hotspot Risk
        hist_data = EnvironmentalDataService.get_historical_waterlogging(rep.ward_id)
        if hist_data.get("is_missing"):
            missing_factors.append("historical_hotspot_data")
            uncertainty_penalty += 3.0
            hist_norm = 40.0
            hist_notes = f"Missing historical data: {hist_data.get('notes')}"
        else:
            hist_norm = float(hist_data.get("historical_score", 40.0))
            hist_notes = f"Ward classification: {hist_data.get('frequency')} frequency. {hist_data.get('notes')}"

        hist_contrib = round(hist_norm * cls.WEIGHT_HISTORICAL, 2)
        factors.append(RiskFactorBreakdown(
            factor_name="Historical Waterlogging Frequency",
            raw_value=hist_data.get("frequency", "UNKNOWN"),
            normalized_score=round(hist_norm, 2),
            weight=cls.WEIGHT_HISTORICAL,
            contribution=hist_contrib,
            is_missing=hist_data.get("is_missing", False),
            notes=hist_notes
        ))

        # 4. Nearby Active Incidents & Recency
        nearby_count = 0
        min_recency_hours = 99.0
        now = datetime.now(timezone.utc)

        if nearby_incidents:
            for other in nearby_incidents:
                if other.id == incident.id:
                    continue
                dist = EnvironmentalDataService.haversine_distance_km(
                    rep.latitude, rep.longitude,
                    other.report.latitude, other.report.longitude
                )
                if dist <= 2.0: # within 2 km radius
                    nearby_count += 1
                    diff_hours = (now - other.created_at).total_seconds() / 3600.0
                    min_recency_hours = min(min_recency_hours, diff_hours)

        if nearby_count == 0:
            min_recency_hours = 0.0

        nearby_norm = cls.normalize_nearby_incidents(nearby_count, min_recency_hours)
        nearby_contrib = round(nearby_norm * cls.WEIGHT_NEARBY, 2)
        factors.append(RiskFactorBreakdown(
            factor_name="Nearby Incidents & Recency",
            raw_value=f"{nearby_count} within 2km",
            normalized_score=round(nearby_norm, 2),
            weight=cls.WEIGHT_NEARBY,
            contribution=nearby_contrib,
            is_missing=False,
            notes=f"Identified {nearby_count} active reports within 2km corridor."
        ))

        # 5. Infrastructure Vulnerability
        infra_data = EnvironmentalDataService.get_infrastructure_vulnerability(rep.ward_id)
        if infra_data.get("is_missing"):
            missing_factors.append("infrastructure_vulnerability")
            uncertainty_penalty += 2.0
            infra_norm = 40.0
            infra_notes = "Missing infrastructure telemetry."
        else:
            infra_norm = float(infra_data.get("vulnerability_score", 40.0))
            assets = ", ".join(infra_data.get("critical_assets", [])) or "Standard urban zone"
            infra_notes = f"Assets: {assets} (Elevation: {infra_data.get('elevation_m', 'N/A')}m)"

        infra_contrib = round(infra_norm * cls.WEIGHT_INFRASTRUCTURE, 2)
        factors.append(RiskFactorBreakdown(
            factor_name="Infrastructure Vulnerability",
            raw_value=infra_data.get("vulnerability_score", 40.0),
            normalized_score=round(infra_norm, 2),
            weight=cls.WEIGHT_INFRASTRUCTURE,
            contribution=infra_contrib,
            is_missing=infra_data.get("is_missing", False),
            notes=infra_notes
        ))

        # Final Deterministic Score Calculation
        total_weighted = sum(f.contribution for f in factors)
        raw_final = total_weighted + uncertainty_penalty
        final_score = min(100.0, max(0.0, round(raw_final, 1)))
        severity = cls.determine_severity(final_score)

        # Audit-Ready Explanation String
        missing_text = f" Warning: Missing factors [{', '.join(missing_factors)}] added +{uncertainty_penalty} uncertainty penalty." if missing_factors else " All sensor & spatial factors verified."
        explanation = (
            f"Calculated Waterlogging Risk Score: {final_score}/100 ({severity.value}). "
            f"Primary drivers: Rainfall ({rain_contribution} pts, {cls.WEIGHT_RAINFALL*100}%), "
            f"Drain Blockage ({block_contrib} pts, {cls.WEIGHT_BLOCKAGE*100}%), "
            f"Historical Hotspot ({hist_contrib} pts, {cls.WEIGHT_HISTORICAL*100}%).{missing_text}"
        )

        return RiskAssessment(
            incident_id=incident.id,
            calculated_at=datetime.now(timezone.utc),
            risk_score=final_score,
            severity=severity,
            factors=factors,
            missing_factors=missing_factors,
            uncertainty_penalty=round(uncertainty_penalty, 1),
            explanation=explanation,
            is_synthetic_data=True
        )
