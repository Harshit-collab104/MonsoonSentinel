from datetime import datetime, timedelta
from app.db.sqlite_repository import get_repository
from app.services.incident_service import IncidentService
from app.models.incident import CitizenReportCreate
from app.core.enums import BlockageSeverity

SEED_REPORTS = [
    {
        "reporter_name": "Aarav Sharma",
        "reporter_phone": "+91-98765-43210",
        "ward_id": "WARD-BLR-01",
        "ward_name": "Bengaluru - Koramangala 80ft Road & Ejipura Outfall",
        "latitude": 12.9345,
        "longitude": 77.6265,
        "drain_blockage_level": BlockageSeverity.COMPLETE,
        "water_depth_cm": 48.0,
        "description": "Severe storm drain blockage near Sony World signal underpass. Plastic debris and silt trapped against primary trash rack. Vehicles stranded.",
        "landmark": "Near Sony World Junction, 80ft Road Koramangala",
        "image_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Priya Nair",
        "reporter_phone": "+91-98111-22334",
        "ward_id": "WARD-BLR-02",
        "ward_name": "Bengaluru - Silk Board Junction & Madiwala Basin",
        "latitude": 12.9172,
        "longitude": 77.6228,
        "drain_blockage_level": BlockageSeverity.SEVERE,
        "water_depth_cm": 38.0,
        "description": "Silk Board flyover ramp culvert overflow spilling onto arterial Hosur road. Silt build-up and tree debris restricting Madiwala outfall flap gate.",
        "landmark": "Opposite Central Silk Board Bus Stop, Hosur Road",
        "image_url": "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Rajesh Kulkarni",
        "reporter_phone": "+91-98222-33445",
        "ward_id": "WARD-BOM-01",
        "ward_name": "Mumbai - Hindmata Cinema & Dadar TT Pumping Station",
        "latitude": 19.0178,
        "longitude": 72.8478,
        "drain_blockage_level": BlockageSeverity.COMPLETE,
        "water_depth_cm": 52.0,
        "description": "Severe inundation under Hindmata Flyover. High tide backflow coupled with heavy cloudburst has overwhelmed storm runoff channels.",
        "landmark": "Hindmata Flyover Underpass, Dadar TT Circle",
        "image_url": "https://images.unsplash.com/photo-1545459720-aac8509eb02c?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Farhan Merchant",
        "reporter_phone": "+91-97666-55443",
        "ward_id": "WARD-BOM-02",
        "ward_name": "Mumbai - Milan Subway & Santacruz West SWD",
        "latitude": 19.0833,
        "longitude": 72.8417,
        "drain_blockage_level": BlockageSeverity.SEVERE,
        "water_depth_cm": 35.0,
        "description": "Milan Subway vehicular underpass submerged. Submersible dewatering pump inlet clogged with floating solid waste.",
        "landmark": "Milan Subway West Entry, SV Road",
        "image_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Sunil Verma",
        "reporter_phone": "+91-99100-11223",
        "ward_id": "WARD-DEL-01",
        "ward_name": "Delhi - Minto Bridge Railway Underpass Basin",
        "latitude": 28.6358,
        "longitude": 77.2255,
        "drain_blockage_level": BlockageSeverity.SEVERE,
        "water_depth_cm": 42.0,
        "description": "Minto Bridge railway underpass water level rising rapidly. Silt choking sump pit and drainage suction lines.",
        "landmark": "Minto Road Railway Bridge, Connaught Place Outer",
        "image_url": None
    },
    {
        "reporter_name": "Kavitha Raman",
        "reporter_phone": "+91-94440-99887",
        "ward_id": "WARD-CHE-01",
        "ward_name": "Chennai - Velachery 100ft Road & Lake Canal",
        "latitude": 12.9792,
        "longitude": 80.2185,
        "drain_blockage_level": BlockageSeverity.PARTIAL,
        "water_depth_cm": 22.0,
        "description": "Runoff bottleneck near Velachery Lake surplus weir. Water accumulating near MRTS railway station approach road.",
        "landmark": "Velachery 100ft Bypass Road near MRTS Station",
        "image_url": None
    },
    {
        "reporter_name": "Vikram Sen",
        "reporter_phone": "+91-97444-55667",
        "ward_id": "WARD-BLR-03",
        "ward_name": "Bengaluru - Bellandur Lake Spillway & Eco-Space Sluice",
        "latitude": 12.9260,
        "longitude": 77.6762,
        "drain_blockage_level": BlockageSeverity.PARTIAL,
        "water_depth_cm": 18.0,
        "description": "Outer Ring Road service lane waterlogged due to weed accumulation at Eco-Space culvert gate.",
        "landmark": "Eco-Space Business Park Main Gate, Outer Ring Road",
        "image_url": "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=600&q=80"
    }
]

def seed_database(force: bool = False):
    repo = get_repository()
    existing = repo.list_all()
    if existing and not force:
        return existing

    service = IncidentService(repo)
    created_incidents = []

    # 1. First Incident: Bengaluru Koramangala -> AWAITING_APPROVAL
    rep1 = CitizenReportCreate(**SEED_REPORTS[0])
    inc1 = service.create_incident(rep1)
    service.analyze_risk(inc1.id)
    service.prioritize_incident(inc1.id)
    service.generate_recommendation(inc1.id)
    service.submit_for_human_approval(inc1.id, "High-priority storm runoff triage complete. Ready for supervisor authorization.")
    created_incidents.append(inc1)

    # 2. Second Incident: Bengaluru Silk Board -> IN_PROGRESS
    rep2 = CitizenReportCreate(**SEED_REPORTS[1])
    inc2 = service.create_incident(rep2)
    service.analyze_risk(inc2.id)
    service.prioritize_incident(inc2.id)
    service.generate_recommendation(inc2.id)
    service.submit_for_human_approval(inc2.id)
    service.review_human_approval(
        inc2.id,
        approved=True,
        reviewer="Chief_Dispatcher_Kapoor",
        rationale="Critical arterial corridor at risk; approved immediate dewatering pump and desilting deployment."
    )
    created_incidents.append(inc2)

    # 3. Third Incident: Mumbai Hindmata -> NEEDS_HUMAN_REVIEW (Walk through to RESOLVED and simulate verification anomaly)
    rep3 = CitizenReportCreate(**SEED_REPORTS[2])
    inc3 = service.create_incident(rep3)
    service.analyze_risk(inc3.id)
    service.prioritize_incident(inc3.id)
    service.generate_recommendation(inc3.id)
    service.submit_for_human_approval(inc3.id)
    service.review_human_approval(
        inc3.id,
        approved=True,
        reviewer="Chief_Dispatcher_Kapoor",
        rationale="Authorized Hindmata rapid response crew."
    )
    service.record_resolution(
        inc3.id,
        resolution_notes="Field crew deployed suction rig and removed 12 cubic meters of silt.",
        evidence_url="s3://monsoon-sentinel-evidence/resolutions/hindmata_clearance.jpg"
    )
    inc3 = service.verify_resolution(
        inc3.id,
        sensor_flow_rate_lps=14.0,
        post_clearance_depth_cm=8.5,
        simulate_failure=True
    )
    created_incidents.append(inc3)

    # 4. Fourth Incident: Mumbai Milan Subway -> ANALYZING
    rep4 = CitizenReportCreate(**SEED_REPORTS[3])
    inc4 = service.create_incident(rep4)
    service.analyze_risk(inc4.id)
    created_incidents.append(inc4)

    # 5. Fifth Incident: Delhi Minto Bridge -> PRIORITIZED
    rep5 = CitizenReportCreate(**SEED_REPORTS[4])
    inc5 = service.create_incident(rep5)
    service.analyze_risk(inc5.id)
    service.prioritize_incident(inc5.id)
    created_incidents.append(inc5)

    # 6. Sixth Incident: Chennai Velachery -> NEW
    rep6 = CitizenReportCreate(**SEED_REPORTS[5])
    inc6 = service.create_incident(rep6)
    created_incidents.append(inc6)

    # 7. Seventh Incident: Bengaluru Bellandur -> NEW
    rep7 = CitizenReportCreate(**SEED_REPORTS[6])
    inc7 = service.create_incident(rep7)
    created_incidents.append(inc7)

    return created_incidents
