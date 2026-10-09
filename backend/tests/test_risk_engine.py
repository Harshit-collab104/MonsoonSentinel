import pytest
from app.models.incident import Incident, CitizenReportCreate
from app.core.enums import BlockageSeverity, Severity
from app.services.risk_engine import RiskEngine

def test_rainfall_normalization():
    assert RiskEngine.normalize_rainfall(0.0) == 0.0
    assert 10.0 <= RiskEngine.normalize_rainfall(10.0) <= 35.0
    assert 35.0 <= RiskEngine.normalize_rainfall(25.0) <= 70.0
    assert RiskEngine.normalize_rainfall(50.0) >= 70.0
    # Missing rainfall fallback
    assert RiskEngine.normalize_rainfall(None) == 40.0

def test_blockage_normalization():
    assert RiskEngine.normalize_blockage(BlockageSeverity.CLEAR) == 0.0
    assert RiskEngine.normalize_blockage(BlockageSeverity.PARTIAL) == 50.0
    assert RiskEngine.normalize_blockage(BlockageSeverity.SEVERE) == 80.0
    assert RiskEngine.normalize_blockage(BlockageSeverity.COMPLETE) == 100.0

def test_deterministic_risk_calculation():
    report = CitizenReportCreate(
        reporter_name="Tester",
        ward_id="WARD-12",
        ward_name="Central Metro",
        latitude=12.9716,
        longitude=77.5946,
        drain_blockage_level=BlockageSeverity.COMPLETE,
        water_depth_cm=45.0,
        description="Drain completely blocked by sediment"
    )
    incident = Incident(report=report)

    # First calculation
    assessment1 = RiskEngine.calculate_risk(incident)
    # Second calculation with identical inputs
    assessment2 = RiskEngine.calculate_risk(incident)

    assert assessment1.risk_score == assessment2.risk_score
    assert assessment1.severity == assessment2.severity
    assert assessment1.severity in [Severity.CRITICAL, Severity.HIGH]
    assert len(assessment1.factors) == 5
    assert assessment1.is_synthetic_data is True

def test_missing_data_tracking():
    # Use a non-existent ward to trigger missing data flags
    report = CitizenReportCreate(
        reporter_name="Tester",
        ward_id="WARD-UNKNOWN-99",
        ward_name="Unregistered Ward",
        latitude=0.0,
        longitude=0.0,
        drain_blockage_level=BlockageSeverity.PARTIAL,
        description="Unknown location reporting waterlogging"
    )
    incident = Incident(report=report)
    assessment = RiskEngine.calculate_risk(incident)

    # Missing factors should be explicitly identified, not silently ignored
    assert len(assessment.missing_factors) > 0
    assert assessment.uncertainty_penalty > 0.0
    assert "Warning: Missing factors" in assessment.explanation
