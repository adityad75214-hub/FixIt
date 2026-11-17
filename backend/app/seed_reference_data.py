"""Idempotently provision generic reference data without demo users or tickets."""
from datetime import datetime, timezone

from app.core.database import get_database


async def seed_reference_data() -> None:
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()

    categories = [
        {"name": "Network and Wi-Fi", "subcategories": ["No Internet Connection", "Slow Speed", "Wi-Fi Authentication Failed", "Coverage Deadzone", "LAN Port Not Working"], "icon": "Wifi"},
        {"name": "Computer and Hardware", "subcategories": ["Desktop Won't Turn On", "Monitor Display Issue", "Mouse/Keyboard Malfunction", "Overheating / Fan Noise", "RAM/SSD Upgrade Required"], "icon": "Monitor"},
        {"name": "Printer and Scanner", "subcategories": ["Paper Jam", "Cartridge Empty / Low Ink", "Printer Offline", "Network Driver Issue", "Scanner Failure"], "icon": "Printer"},
        {"name": "Projector and Smart Classroom", "subcategories": ["No HDMI Signal", "Dim / Blurry Projection", "Audio System Silent", "Interactive Board Sensor Broken", "Remote Missing"], "icon": "Tv"},
        {"name": "Software and Applications", "subcategories": ["MATLAB / AutoCAD License Error", "OS Crashing / Blue Screen", "Antivirus Blocked App", "LMS Portal Login Error", "Software Installation Request"], "icon": "Code"},
        {"name": "Laboratory Equipment", "subcategories": ["Microcontroller Programmer Fault", "Oscilloscope Power Supply", "Server Rack Power Issue", "Lab Workstation Unresponsive"], "icon": "Cpu"},
        {"name": "Account and Login", "subcategories": ["Forgot Password", "Account Locked", "Two-Factor Auth Reset", "ID Card NFC Access Denied"], "icon": "Shield"},
    ]
    for category in categories:
        doc = {
            **category,
            "description": f"Issues relating to campus {category['name'].lower()}",
            "is_active": True,
        }
        await db.categories.update_one(
            {"name": category["name"]},
            {"$setOnInsert": doc},
            upsert=True,
        )

    policies = [
        {"priority": "critical", "target_resolution_hours": 2, "target_response_hours": 1, "description": "Campus-wide outages, server failures, smart classroom during ongoing lecture"},
        {"priority": "high", "target_resolution_hours": 8, "target_response_hours": 2, "description": "Lab equipment for scheduled classes, Wi-Fi outage in entire floor/wing"},
        {"priority": "medium", "target_resolution_hours": 24, "target_response_hours": 4, "description": "Individual workstation issues, departmental printer failures"},
        {"priority": "low", "target_resolution_hours": 72, "target_response_hours": 8, "description": "Routine software requests, general inquiries, minor glitches"},
    ]
    for policy in policies:
        await db.sla_policies.update_one(
            {"priority": policy["priority"]},
            {"$setOnInsert": {**policy, "updated_at": now_iso}},
            upsert=True,
        )
