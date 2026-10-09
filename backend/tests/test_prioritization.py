import pytest
from app.models.incident import Incident, CitizenReportCreate
from app.core.enums import BlockageSeverity
from app.services.prioritization import PrioritizationService
from app.services.risk_engine import RiskEngine

def test_urgency_scoring():
    rep_high = CitizenReportCreate(
        reporter_name="High Priority",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.COMPLETE,
        water_depth_cm=50.0,
        description="Submerged underpass"
    )
    inc_high = Incident(report=rep_high)
    inc_high.risk_assessment = RiskEngine.calculate_risk(inc_high)

    rep_low = CitizenReportCreate(
        reporter_name="Low Priority",
        ward_id="WARD-19",
        ward_name="Eastern Hills",
        latitude=12.9850,
        longitude=77.6680,
        drain_blockage_level=BlockageSeverity.CLEAR,
        water_depth_cm=5.0,
        description="Minor puddling"
    )
    inc_low = Incident(report=rep_low)
    inc_low.risk_assessment = RiskEngine.calculate_risk(inc_low)

    urgency_high = PrioritizationService.calculate_urgency(inc_high)
    urgency_low = PrioritizationService.calculate_urgency(inc_low)

    assert urgency_high > urgency_low

def test_ranking_multiple_incidents():
    incidents = []
    for i, blockage in enumerate([BlockageSeverity.CLEAR, BlockageSeverity.COMPLETE, BlockageSeverity.PARTIAL]):
        rep = CitizenReportCreate(
            reporter_name=f"User {i}",
            ward_id="WARD-12",
            ward_name="Central Metro",
            latitude=12.9716,
            longitude=77.5946,
            drain_blockage_level=blockage,
            water_depth_cm=10.0 * (i + 1),
            description=f"Incident test {i}"
        )
        inc = Incident(report=rep)
        inc.risk_assessment = RiskEngine.calculate_risk(inc)
        incidents.append(inc)

    ranked = PrioritizationService.rank_incidents(incidents)
    assert len(ranked) == 3
    assert ranked[0].priority.priority_rank == 1
    assert ranked[1].priority.priority_rank == 2
    assert ranked[2].priority.priority_rank == 3
    assert ranked[0].priority.urgency_score >= ranked[1].priority.urgency_score >= ranked[2].priority.urgency_score
