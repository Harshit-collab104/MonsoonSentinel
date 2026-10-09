from datetime import datetime, timedelta
from app.db.sqlite_repository import get_repository
from app.services.incident_service import IncidentService
from app.models.incident import CitizenReportCreate
from app.core.enums import BlockageSeverity

SEED_REPORTS = [
    {
        "reporter_name": "Aarav Sharma",
        "reporter_phone": "+91-98765-43210",
        "ward_id": "WARD-12",
        "ward_name": "Central Metro & Commercial Hub",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "drain_blockage_level": BlockageSeverity.COMPLETE,
        "water_depth_cm": 45.0,
        "description": "Severe storm drain blockage near Metro Gate 3 underpass. Plastic debris and construction runoff trapped against primary trash rack. Vehicles stranded.",
        "landmark": "Near Metro Pillar 142",
        "image_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Priya Nair",
        "reporter_phone": "+91-98111-22334",
        "ward_id": "WARD-07",
        "ward_name": "South Lakeside & Riverfront Drainage Basin",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "drain_blockage_level": BlockageSeverity.SEVERE,
        "water_depth_cm": 32.0,
        "description": "Lakeside culvert overflow spilling onto arterial connecting road. Silt build-up and tree branches restricting outfall flap gate.",
        "landmark": "Opposite Lakeside Hospital Emergency Gate",
        "image_url": "https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Vikram Sen",
        "reporter_phone": "+91-97444-55667",
        "ward_id": "WARD-04",
        "ward_name": "North Industrial Estate & Culvert Zone",
        "latitude": 13.0358,
        "longitude": 77.5970,
        "drain_blockage_level": BlockageSeverity.PARTIAL,
        "water_depth_cm": 18.0,
        "description": "Industrial bypass drain running slow due to packaging waste. Pooling along warehouse access lane.",
        "landmark": "Plot 42 Warehouse Complex",
        "image_url": "https://images.unsplash.com/photo-1545459720-aac8509eb02c?auto=format&fit=crop&w=600&q=80"
    },
    {
        "reporter_name": "Meera Joshi",
        "reporter_phone": "+91-96555-88990",
        "ward_id": "WARD-19",
        "ward_name": "Eastern Hills Residential Heights",
        "latitude": 12.9850,
        "longitude": 77.6680,
        "drain_blockage_level": BlockageSeverity.CLEAR,
        "water_depth_cm": 8.0,
        "description": "Minor surface runoff accumulation along downhill curb. Grate is clean but runoff volume is high during peak cloudburst.",
        "landmark": "Corner of 5th Main & Green Avenue",
        "image_url": None
    }
]

def seed_database(force: bool = False):
    repo = get_repository()
    existing = repo.list_all()
    if existing and not force:
        return existing

    service = IncidentService(repo)
    created_incidents = []

    # 1. First Incident: Walk through to AWAITING_APPROVAL
    rep1 = CitizenReportCreate(**SEED_REPORTS[0])
    inc1 = service.create_incident(rep1)
    service.analyze_risk(inc1.id)
    service.prioritize_incident(inc1.id)
    service.generate_recommendation(inc1.id)
    service.submit_for_human_approval(inc1.id, "High-priority flood triage complete. Ready for supervisor authorization.")
    created_incidents.append(inc1)

    # 2. Second Incident: Walk through to IN_PROGRESS
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
        rationale="Hospital corridor at risk; approved immediate dewatering pump deployment."
    )
    created_incidents.append(inc2)

    # 3. Third Incident: Just ANALYZED
    rep3 = CitizenReportCreate(**SEED_REPORTS[2])
    inc3 = service.create_incident(rep3)
    service.analyze_risk(inc3.id)
    created_incidents.append(inc3)

    # 4. Fourth Incident: Brand NEW
    rep4 = CitizenReportCreate(**SEED_REPORTS[3])
    inc4 = service.create_incident(rep4)
    created_incidents.append(inc4)

    return created_incidents
