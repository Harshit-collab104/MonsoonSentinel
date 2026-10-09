from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.models.incident import Incident
from app.models.risk import PriorityScore
from app.core.enums import Severity, BlockageSeverity

class PrioritizationService:
    """Ranks and prioritizes waterlogging incidents by operational urgency.
    Considers risk score, water depth, blockage severity, and report age.
    """

    @classmethod
    def calculate_urgency(cls, incident: Incident) -> float:
        risk_score = incident.risk_assessment.risk_score if incident.risk_assessment else 50.0

        # Depth factor (cm): > 30 cm is hazardous for pedestrian & vehicular traffic
        depth_cm = incident.report.water_depth_cm or 0.0
        depth_multiplier = 1.0 + min(0.5, depth_cm / 100.0)

        # Blockage boost
        blockage_boost = 0.0
        if incident.report.drain_blockage_level == BlockageSeverity.COMPLETE:
            blockage_boost = 15.0
        elif incident.report.drain_blockage_level == BlockageSeverity.SEVERE:
            blockage_boost = 8.0

        # Report age urgency: unattended incidents gain urgency over hours
        age_hours = (datetime.now(timezone.utc) - incident.created_at).total_seconds() / 3600.0
        age_boost = min(10.0, age_hours * 2.0)

        raw_urgency = (risk_score * depth_multiplier) + blockage_boost + age_boost
        return round(raw_urgency, 1)

    @classmethod
    def rank_incidents(cls, incidents: List[Incident]) -> List[Incident]:
        """Ranks a list of incidents in descending order of urgency score, assigning priority ranks."""
        scored = []
        for inc in incidents:
            urgency = cls.calculate_urgency(inc)
            scored.append((urgency, inc))

        # Sort descending by urgency score
        scored.sort(key=lambda x: x[0], reverse=True)

        ranked_incidents = []
        for rank, (urgency, inc) in enumerate(scored, start=1):
            severity_str = inc.risk_assessment.severity.value if inc.risk_assessment else "UNKNOWN"
            depth_val = inc.report.water_depth_cm or 0.0
            inc.priority = PriorityScore(
                incident_id=inc.id,
                priority_rank=rank,
                urgency_score=urgency,
                evaluated_at=datetime.now(timezone.utc),
                ranking_factors={
                    "risk_score": inc.risk_assessment.risk_score if inc.risk_assessment else None,
                    "water_depth_cm": depth_val,
                    "blockage_level": inc.report.drain_blockage_level.value,
                    "rank": rank,
                    "total_active_queue_size": len(incidents)
                },
                recommendation_summary=f"Rank #{rank} (Urgency: {urgency}) - {severity_str} severity in {inc.report.ward_name}."
            )
            ranked_incidents.append(inc)

        return ranked_incidents

    @classmethod
    def prioritize_single(cls, incident: Incident, all_active: Optional[List[Incident]] = None) -> PriorityScore:
        """Prioritizes a single incident relative to the active queue."""
        active_list = all_active or []
        if incident not in active_list and not any(i.id == incident.id for i in active_list):
            active_list = [incident] + [i for i in active_list if i.id != incident.id]

        ranked = cls.rank_incidents(active_list)
        for r in ranked:
            if r.id == incident.id:
                incident.priority = r.priority
                return r.priority

        # Fallback
        urgency = cls.calculate_urgency(incident)
        p = PriorityScore(
            incident_id=incident.id,
            priority_rank=1,
            urgency_score=urgency,
            evaluated_at=datetime.now(timezone.utc),
            ranking_factors={"risk_score": incident.risk_assessment.risk_score if incident.risk_assessment else 50.0},
            recommendation_summary=f"Urgency score: {urgency}"
        )
        incident.priority = p
        return p
