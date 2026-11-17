import asyncio
from datetime import datetime, timezone, timedelta
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.core.security import get_password_hash
from pymongo.errors import DuplicateKeyError


async def _insert_seed_if_missing(collection, document, identity_fields=("_id",)):
    """Insert demo data only when no matching record exists; never overwrite live data."""
    identity = [{field: document[field]} for field in identity_fields if field in document]
    if identity and await collection.find_one({"$or": identity}):
        return False
    try:
        await collection.insert_one(document)
        return True
    except DuplicateKeyError:
        # Another record may have claimed a unique key between the check and insert.
        return False

async def seed_data():
    from app.core.config import settings
    if settings.is_production:
        raise RuntimeError("Demo seed data is prohibited in production.")
    print("[*] Checking database for seeding...")
    # Do not call connect_to_mongo() here if already connected to db
    db = get_database()
    if db is None:
        await connect_to_mongo()
        db = get_database()

    # Check if admin is already seeded
    existing_admin = await db.users.find_one({"role": "admin"})
    if existing_admin:
        # Database already has an admin, do not overwrite existing users or re-seed
        return

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # 1. Seed Users (Admin, Staff, Faculty, Student)
    users = [
        {
            "_id": "USR-ADMIN-001",
            "email": "admin@college.edu",
            "password_hash": get_password_hash("Admin@123"),
            "name": "Dr. Sarah Jenkins",
            "role": "admin",
            "department": "Campus IT Administration",
            "phone": "+1 (555) 019-2831",
            "identifier": "ADM-9001",
            "specialization": ["Administration", "Security"],
            "is_active": True,
            "created_at": (now - timedelta(days=90)).isoformat()
        },
        {
            "_id": "USR-STAFF-001",
            "email": "staff.network@college.edu",
            "password_hash": get_password_hash("Staff@123"),
            "name": "Alex Rivera",
            "role": "staff",
            "department": "Network Operations",
            "phone": "+1 (555) 019-4451",
            "identifier": "STF-201",
            "specialization": ["Network and Wi-Fi", "Server and Infrastructure"],
            "is_active": True,
            "created_at": (now - timedelta(days=60)).isoformat()
        },
        {
            "_id": "USR-STAFF-002",
            "email": "staff.hardware@college.edu",
            "password_hash": get_password_hash("Staff@123"),
            "name": "Marcus Chen",
            "role": "staff",
            "department": "Hardware Support",
            "phone": "+1 (555) 019-8822",
            "identifier": "STF-202",
            "specialization": ["Computer and Hardware", "Printer and Scanner", "Projector and Smart Classroom"],
            "is_active": True,
            "created_at": (now - timedelta(days=60)).isoformat()
        },
        {
            "_id": "USR-STAFF-003",
            "email": "staff.software@college.edu",
            "password_hash": get_password_hash("Staff@123"),
            "name": "Priya Patel",
            "role": "staff",
            "department": "Systems & Applications",
            "phone": "+1 (555) 019-3319",
            "identifier": "STF-203",
            "specialization": ["Software and Applications", "Account and Login", "Laboratory Equipment"],
            "is_active": True,
            "created_at": (now - timedelta(days=45)).isoformat()
        },
        {
            "_id": "USR-FACULTY-001",
            "email": "prof.sharma@college.edu",
            "password_hash": get_password_hash("Faculty@123"),
            "name": "Prof. Rajesh Sharma",
            "role": "faculty",
            "department": "Computer Science & Engineering",
            "phone": "+1 (555) 019-7762",
            "identifier": "FAC-104",
            "specialization": [],
            "is_active": True,
            "created_at": (now - timedelta(days=30)).isoformat()
        },
        {
            "_id": "USR-STUDENT-001",
            "email": "rahul.student@college.edu",
            "password_hash": get_password_hash("Student@123"),
            "name": "Rahul Verma",
            "role": "student",
            "department": "Electrical Engineering",
            "phone": "+1 (555) 019-5501",
            "identifier": "STU-2024-041",
            "specialization": [],
            "is_active": True,
            "created_at": (now - timedelta(days=20)).isoformat()
        }
    ]

    for u in users:
        await _insert_seed_if_missing(db.users, u, ("_id", "email"))
    print("[OK] Seeded 6 users.")

    # 2. Seed Campus Hierarchy (Campus -> Building -> Floor -> Room)
    campus = {
        "_id": "CAMPUS-MAIN",
        "name": "Main University Campus",
        "code": "MAIN",
        "is_active": True
    }
    await _insert_seed_if_missing(db.campuses, campus)

    # Buildings with distinct floor counts as required:
    # Building A: 2 floors, Building B: 4 floors, Science Lab Complex: 5 floors
    buildings = [
        {"_id": "BLD-ADM", "campus_id": "CAMPUS-MAIN", "name": "Administrative Building", "code": "ADM", "total_floors": 2, "is_active": True, "order": 1},
        {"_id": "BLD-ENG", "campus_id": "CAMPUS-MAIN", "name": "Engineering Block", "code": "ENG", "total_floors": 4, "is_active": True, "order": 2},
        {"_id": "BLD-SCI", "campus_id": "CAMPUS-MAIN", "name": "Science & Research Complex", "code": "SCI", "total_floors": 5, "is_active": True, "order": 3},
        {"_id": "BLD-LIB", "campus_id": "CAMPUS-MAIN", "name": "Central Library", "code": "LIB", "total_floors": 3, "is_active": True, "order": 4}
    ]
    for b in buildings:
        await _insert_seed_if_missing(db.buildings, b)

    floors = [
        # Administrative Building (2 floors)
        {"_id": "FLR-ADM-0", "building_id": "BLD-ADM", "floor_number": 0, "floor_name": "Ground Floor", "order": 0, "is_active": True},
        {"_id": "FLR-ADM-1", "building_id": "BLD-ADM", "floor_number": 1, "floor_name": "1st Floor", "order": 1, "is_active": True},

        # Engineering Block (4 floors)
        {"_id": "FLR-ENG-0", "building_id": "BLD-ENG", "floor_number": 0, "floor_name": "Ground Floor", "order": 0, "is_active": True},
        {"_id": "FLR-ENG-1", "building_id": "BLD-ENG", "floor_number": 1, "floor_name": "1st Floor", "order": 1, "is_active": True},
        {"_id": "FLR-ENG-2", "building_id": "BLD-ENG", "floor_number": 2, "floor_name": "2nd Floor", "order": 2, "is_active": True},
        {"_id": "FLR-ENG-3", "building_id": "BLD-ENG", "floor_number": 3, "floor_name": "3rd Floor", "order": 3, "is_active": True},

        # Science & Research Complex (5 floors)
        {"_id": "FLR-SCI-0", "building_id": "BLD-SCI", "floor_number": 0, "floor_name": "Ground Floor", "order": 0, "is_active": True},
        {"_id": "FLR-SCI-1", "building_id": "BLD-SCI", "floor_number": 1, "floor_name": "1st Floor", "order": 1, "is_active": True},
        {"_id": "FLR-SCI-2", "building_id": "BLD-SCI", "floor_number": 2, "floor_name": "2nd Floor", "order": 2, "is_active": True},
        {"_id": "FLR-SCI-3", "building_id": "BLD-SCI", "floor_number": 3, "floor_name": "3rd Floor", "order": 3, "is_active": True},
        {"_id": "FLR-SCI-4", "building_id": "BLD-SCI", "floor_number": 4, "floor_name": "4th Floor", "order": 4, "is_active": True},

        # Central Library (3 floors)
        {"_id": "FLR-LIB-0", "building_id": "BLD-LIB", "floor_number": 0, "floor_name": "Ground Floor", "order": 0, "is_active": True},
        {"_id": "FLR-LIB-1", "building_id": "BLD-LIB", "floor_number": 1, "floor_name": "1st Floor", "order": 1, "is_active": True},
        {"_id": "FLR-LIB-2", "building_id": "BLD-LIB", "floor_number": 2, "floor_name": "2nd Floor", "order": 2, "is_active": True}
    ]
    for f in floors:
        await _insert_seed_if_missing(db.floors, f)

    rooms = [
        # Administrative Building Rooms
        {"_id": "RM-ADM-001", "building_id": "BLD-ADM", "floor_id": "FLR-ADM-0", "room_number": "101", "room_name": "Registrar Office", "department": "Administration", "is_active": True},
        {"_id": "RM-ADM-002", "building_id": "BLD-ADM", "floor_id": "FLR-ADM-0", "room_number": "102", "room_name": "Campus Data Center", "department": "IT Administration", "is_active": True},
        {"_id": "RM-ADM-101", "building_id": "BLD-ADM", "floor_id": "FLR-ADM-1", "room_number": "201", "room_name": "Dean Conference Room", "department": "Administration", "is_active": True},

        # Engineering Block Rooms
        {"_id": "RM-ENG-001", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-0", "room_number": "G01", "room_name": "Computer Systems Lab A", "department": "Computer Science & Engineering", "is_active": True},
        {"_id": "RM-ENG-002", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-0", "room_number": "G02", "room_name": "Hardware Workshop", "department": "Electrical Engineering", "is_active": True},
        {"_id": "RM-ENG-101", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-1", "room_number": "101", "room_name": "Smart Classroom 101", "department": "Computer Science & Engineering", "is_active": True},
        {"_id": "RM-ENG-102", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-1", "room_number": "102", "room_name": "Embedded Systems Lab", "department": "Electrical Engineering", "is_active": True},
        {"_id": "RM-ENG-201", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-2", "room_number": "204", "room_name": "Lecture Theater 2", "department": "Engineering General", "is_active": True},
        {"_id": "RM-ENG-301", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-3", "room_number": "310", "room_name": "Faculty Research Offices", "department": "Computer Science & Engineering", "is_active": True},

        # Science Complex Rooms
        {"_id": "RM-SCI-001", "building_id": "BLD-SCI", "floor_id": "FLR-SCI-0", "room_number": "SC-G1", "room_name": "Auditorium & Seminar Hall", "department": "Science & Humanities", "is_active": True},
        {"_id": "RM-SCI-101", "building_id": "BLD-SCI", "floor_id": "FLR-SCI-1", "room_number": "SC-101", "room_name": "Physics Computing Lab", "department": "Physics", "is_active": True},
        {"_id": "RM-SCI-201", "building_id": "BLD-SCI", "floor_id": "FLR-SCI-2", "room_number": "SC-201", "room_name": "Chemical Instruments Room", "department": "Chemistry", "is_active": True},
        {"_id": "RM-SCI-301", "building_id": "BLD-SCI", "floor_id": "FLR-SCI-3", "room_number": "SC-301", "room_name": "Bio-Informatics Workstation Lab", "department": "Biotechnology", "is_active": True},
        {"_id": "RM-SCI-401", "building_id": "BLD-SCI", "floor_id": "FLR-SCI-4", "room_number": "SC-401", "room_name": "High Performance Computing (HPC) Center", "department": "IT Operations", "is_active": True},

        # Library Rooms
        {"_id": "RM-LIB-001", "building_id": "BLD-LIB", "floor_id": "FLR-LIB-0", "room_number": "L-01", "room_name": "Circulation Desk & E-Resources", "department": "Library Services", "is_active": True},
        {"_id": "RM-LIB-101", "building_id": "BLD-LIB", "floor_id": "FLR-LIB-1", "room_number": "L-101", "room_name": "Digital Research Lab", "department": "Library Services", "is_active": True},
        {"_id": "RM-LIB-201", "building_id": "BLD-LIB", "floor_id": "FLR-LIB-2", "room_number": "L-201", "room_name": "Quiet Study & Online Terminals", "department": "Library Services", "is_active": True}
    ]
    for r in rooms:
        await _insert_seed_if_missing(db.rooms, r)
    print(f"[OK] Seeded Campus hierarchy: {len(buildings)} buildings, {len(floors)} floors, {len(rooms)} rooms.")

    # 3. Seed Complaint Categories
    categories = [
        {"name": "Network and Wi-Fi", "subcategories": ["No Internet Connection", "Slow Speed", "Wi-Fi Authentication Failed", "Coverage Deadzone", "LAN Port Not Working"], "icon": "Wifi"},
        {"name": "Computer and Hardware", "subcategories": ["Desktop Won't Turn On", "Monitor Display Issue", "Mouse/Keyboard Malfunction", "Overheating / Fan Noise", "RAM/SSD Upgrade Required"], "icon": "Monitor"},
        {"name": "Printer and Scanner", "subcategories": ["Paper Jam", "Cartridge Empty / Low Ink", "Printer Offline", "Network Driver Issue", "Scanner Failure"], "icon": "Printer"},
        {"name": "Projector and Smart Classroom", "subcategories": ["No HDMI Signal", "Dim / Blurry Projection", "Audio System Silent", "Interactive Board Sensor Broken", "Remote Missing"], "icon": "Tv"},
        {"name": "Software and Applications", "subcategories": ["MATLAB / AutoCAD License Error", "OS Crashing / Blue Screen", "Antivirus Blocked App", "LMS Portal Login Error", "Software Installation Request"], "icon": "Code"},
        {"name": "Laboratory Equipment", "subcategories": ["Microcontroller Programmer Fault", "Oscilloscope Power Supply", "Server Rack Power Issue", "Lab Workstation Unresponsive"], "icon": "Cpu"},
        {"name": "Account and Login", "subcategories": ["Forgot Password", "Account Locked", "Two-Factor Auth Reset", "ID Card NFC Access Denied"], "icon": "Shield"}
    ]
    for c in categories:
        category_doc = {
            "name": c["name"],
            "subcategories": c["subcategories"],
            "description": f"Issues relating to campus {c['name'].lower()}",
            "is_active": True,
            "icon": c["icon"],
        }
        await _insert_seed_if_missing(db.categories, category_doc, ("name",))
    print(f"[OK] Seeded {len(categories)} categories.")

    # 4. Seed SLA Policies
    sla_policies = [
        {"priority": "critical", "target_resolution_hours": 2, "target_response_hours": 1, "description": "Campus-wide outages, server failures, smart classroom during ongoing lecture"},
        {"priority": "high", "target_resolution_hours": 8, "target_response_hours": 2, "description": "Lab equipment for scheduled classes, Wi-Fi outage in entire floor/wing"},
        {"priority": "medium", "target_resolution_hours": 24, "target_response_hours": 4, "description": "Individual workstation issues, departmental printer failures"},
        {"priority": "low", "target_resolution_hours": 72, "target_response_hours": 8, "description": "Routine software requests, general inquiries, minor glitches"}
    ]
    for p in sla_policies:
        policy_doc = {**p, "updated_at": now_iso}
        await _insert_seed_if_missing(db.sla_policies, policy_doc, ("priority",))
    print("[OK] Seeded SLA policies.")

    # 5. Seed Knowledge Base Articles
    articles = [
        {
            "_id": "KB-ART-001",
            "title": "How to Connect to Campus High-Speed Wi-Fi (Eduroam)",
            "category": "Network and Wi-Fi",
            "content": "To connect your laptop or mobile device to the official campus Wi-Fi network:\n\n1. Enable Wi-Fi on your device and select 'Eduroam' or 'Campus-Secure'.\n2. When prompted for EAP Method, select 'PEAP'.\n3. Phase 2 authentication should be set to 'MSCHAPV2'.\n4. CA Certificate: Select 'Do not validate' or use system certificates.\n5. Identity: Enter your full college email address (e.g. rahul.student@college.edu).\n6. Password: Enter your campus portal password.\n7. Click Connect. If you encounter authentication timeouts, clear saved networks and re-enter credentials.",
            "tags": ["wifi", "eduroam", "network", "internet"],
            "views": 420,
            "helpful_count": 89,
            "not_helpful_count": 3,
            "author_name": "Alex Rivera",
            "is_published": True,
            "created_at": (now - timedelta(days=40)).isoformat(),
            "updated_at": now_iso
        },
        {
            "_id": "KB-ART-002",
            "title": "Troubleshooting Classroom Projector HDMI and Audio Output",
            "category": "Projector and Smart Classroom",
            "content": "If the ceiling projector in your classroom displays 'No Signal' or has no sound:\n\n1. Ensure the wall podium control panel is powered ON (Green indicator).\n2. Press 'Laptop / HDMI 1' on the switcher button.\n3. On Windows, press `Windows Key + P` and choose 'Duplicate' or 'Extend'.\n4. For Mac: Open System Settings -> Displays -> Arrangement, and ensure Mirror Display is enabled.\n5. If sound is missing: Right-click the speaker icon in Windows -> Sound Output -> Select 'Crestron Audio / Extron Audio'.\n6. If the lamp warning light flashes amber, submit a Critical ticket immediately for lamp replacement.",
            "tags": ["projector", "hdmi", "smart classroom", "audio", "display"],
            "views": 310,
            "helpful_count": 64,
            "not_helpful_count": 2,
            "author_name": "Marcus Chen",
            "is_published": True,
            "created_at": (now - timedelta(days=35)).isoformat(),
            "updated_at": now_iso
        },
        {
            "_id": "KB-ART-003",
            "title": "Resetting Forgotten College Portal and LMS Passwords",
            "category": "Account and Login",
            "content": "If you are locked out of the student or faculty portal:\n\n1. Visit the portal login page and click 'Forgot Password?'.\n2. Enter your registered institutional email address or student roll number.\n3. A one-time verification link will be sent to your alternative email or SMS.\n4. Ensure your new password contains at least 8 characters, with 1 uppercase, 1 numeral, and 1 special symbol.\n5. Note: Active Directory synchronizes password changes within 15 minutes across Wi-Fi, LMS, and lab computers.",
            "tags": ["password", "login", "portal", "account"],
            "views": 580,
            "helpful_count": 142,
            "not_helpful_count": 5,
            "author_name": "Priya Patel",
            "is_published": True,
            "created_at": (now - timedelta(days=50)).isoformat(),
            "updated_at": now_iso
        }
    ]
    for a in articles:
        await _insert_seed_if_missing(db.knowledge_base, a)
    print(f"[OK] Seeded {len(articles)} knowledge base articles.")

    # 6. Seed Sample Tickets
    tickets = [
        {
            "_id": "TCK-SEED-001",
            "ticket_id": f"FIXIT-{now.year}-0001",
            "title": "Ceiling Projector HDMI Port Loose in Smart Classroom 101",
            "description": "During the morning lecture, the HDMI connection kept blinking. The cable port on the podium appears loose and drops audio periodically.",
            "category": "Projector and Smart Classroom",
            "subcategory": "No HDMI Signal",
            "priority": "high",
            "status": "in_progress",
            "campus_id": "CAMPUS-MAIN",
            "building": "Engineering Block",
            "floor": "1st Floor",
            "room": "101",
            "department": "Computer Science & Engineering",
            "affected_users": 65,
            "attachments": [],
            "created_by": {
                "id": "USR-FACULTY-001",
                "name": "Prof. Rajesh Sharma",
                "email": "prof.sharma@college.edu",
                "role": "faculty"
            },
            "assigned_to": {
                "id": "USR-STAFF-002",
                "name": "Marcus Chen",
                "email": "staff.hardware@college.edu",
                "role": "staff"
            },
            "created_at": (now - timedelta(hours=6)).isoformat(),
            "updated_at": (now - timedelta(hours=2)).isoformat(),
            "sla_deadline": (now + timedelta(hours=2)).isoformat(),
            "sla_target_hours": 8,
            "is_overdue": False,
            "time_remaining_minutes": 120,
            "first_response_at": (now - timedelta(hours=5)).isoformat(),
            "resolved_at": None,
            "closed_at": None,
            "resolution_notes": None,
            "hold_reason": None,
            "timeline": [
                {
                    "action": "TICKET_CREATED",
                    "actor_name": "Prof. Rajesh Sharma",
                    "actor_role": "faculty",
                    "actor_id": "USR-FACULTY-001",
                    "timestamp": (now - timedelta(hours=6)).isoformat(),
                    "note": "Reported issue with classroom projector"
                },
                {
                    "action": "ASSIGNED",
                    "actor_name": "Dr. Sarah Jenkins",
                    "actor_role": "admin",
                    "actor_id": "USR-ADMIN-001",
                    "timestamp": (now - timedelta(hours=5)).isoformat(),
                    "note": "Assigned to Marcus Chen (Hardware Team)"
                },
                {
                    "action": "STATUS_CHANGED",
                    "actor_name": "Marcus Chen",
                    "actor_role": "staff",
                    "actor_id": "USR-STAFF-002",
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "old_value": "assigned",
                    "new_value": "in_progress",
                    "note": "Inspecting classroom hardware during break"
                }
            ],
            "has_feedback": False,
            "linked_incident_id": None
        },
        {
            "_id": "TCK-SEED-002",
            "ticket_id": f"FIXIT-{now.year}-0002",
            "title": "Wi-Fi Authentication Timeout in Central Library 1st Floor",
            "description": "Laptops fail to connect to Eduroam with error 'Authentication Failed' even with correct portal credentials. Affecting entire study area.",
            "category": "Network and Wi-Fi",
            "subcategory": "Wi-Fi Authentication Failed",
            "priority": "critical",
            "status": "resolved",
            "campus_id": "CAMPUS-MAIN",
            "building": "Central Library",
            "floor": "1st Floor",
            "room": "L-101",
            "department": "Library Services",
            "affected_users": 120,
            "attachments": [],
            "created_by": {
                "id": "USR-STUDENT-001",
                "name": "Rahul Verma",
                "email": "rahul.student@college.edu",
                "role": "student"
            },
            "assigned_to": {
                "id": "USR-STAFF-001",
                "name": "Alex Rivera",
                "email": "staff.network@college.edu",
                "role": "staff"
            },
            "created_at": (now - timedelta(hours=14)).isoformat(),
            "updated_at": (now - timedelta(hours=8)).isoformat(),
            "sla_deadline": (now - timedelta(hours=12)).isoformat(),
            "sla_target_hours": 2,
            "is_overdue": False,
            "time_remaining_minutes": 0,
            "first_response_at": (now - timedelta(hours=13, minutes=30)).isoformat(),
            "resolved_at": (now - timedelta(hours=8)).isoformat(),
            "closed_at": None,
            "resolution_notes": "Rebooted access point AP-LIB-04 and renewed RADIUS certificates.",
            "hold_reason": None,
            "timeline": [
                {
                    "action": "TICKET_CREATED",
                    "actor_name": "Rahul Verma",
                    "actor_role": "student",
                    "actor_id": "USR-STUDENT-001",
                    "timestamp": (now - timedelta(hours=14)).isoformat(),
                    "note": "Created Wi-Fi outage ticket"
                },
                {
                    "action": "ASSIGNED",
                    "actor_name": "System Auto-Assign",
                    "actor_role": "system",
                    "actor_id": "SYSTEM",
                    "timestamp": (now - timedelta(hours=13, minutes=50)).isoformat(),
                    "note": "Auto-routed to Network specialist Alex Rivera"
                },
                {
                    "action": "RESOLVED",
                    "actor_name": "Alex Rivera",
                    "actor_role": "staff",
                    "actor_id": "USR-STAFF-001",
                    "timestamp": (now - timedelta(hours=8)).isoformat(),
                    "note": "RADIUS cert updated and AP re-initialized."
                }
            ],
            "has_feedback": True,
            "linked_incident_id": None
        }
    ]

    for t in tickets:
        await _insert_seed_if_missing(db.tickets, t, ("_id", "ticket_id"))
    print(f"[OK] Seeded {len(tickets)} sample tickets.")

    # 7. Seed Comments (including public vs internal note)
    comments = [
        {
            "_id": "CMT-SEED-001",
            "ticket_id": f"FIXIT-{now.year}-0001",
            "ticket_db_id": "TCK-SEED-001",
            "author": {
                "id": "USR-STAFF-002",
                "name": "Marcus Chen",
                "email": "staff.hardware@college.edu",
                "role": "staff"
            },
            "content": "I have tested the wall port. The female HDMI header pins are bent. I will replace the wall faceplate today at 2:00 PM.",
            "is_internal": False,
            "attachments": [],
            "created_at": (now - timedelta(hours=3)).isoformat()
        },
        {
            "_id": "CMT-SEED-002",
            "ticket_id": f"FIXIT-{now.year}-0001",
            "ticket_db_id": "TCK-SEED-001",
            "author": {
                "id": "USR-STAFF-002",
                "name": "Marcus Chen",
                "email": "staff.hardware@college.edu",
                "role": "staff"
            },
            "content": "INTERNAL NOTE: Spoke with vendor Extron. Spare modular faceplate in stock in room 310 IT storage drawer B.",
            "is_internal": True,
            "attachments": [],
            "created_at": (now - timedelta(hours=2, minutes=30)).isoformat()
        }
    ]
    for c in comments:
        await _insert_seed_if_missing(db.comments, c)
    print("[OK] Seeded sample comments & internal notes.")

    # 8. Seed Feedback
    feedback = [
        {
            "_id": "FDB-SEED-001",
            "ticket_id": f"FIXIT-{now.year}-0002",
            "ticket_custom_id": f"FIXIT-{now.year}-0002",
            "ticket_db_id": "TCK-SEED-002",
            "rating": 5,
            "comments": "The IT team fixed the library Wi-Fi very quickly! Speeds are consistent now. Great job!",
            "created_by": {
                "id": "USR-STUDENT-001",
                "name": "Rahul Verma",
                "email": "rahul.student@college.edu",
                "role": "student"
            },
            "created_at": (now - timedelta(hours=4)).isoformat()
        }
    ]
    for f in feedback:
        await _insert_seed_if_missing(db.feedback, f)
    print("[OK] Seeded sample feedback.")

    await close_mongo_connection()
    print("[SUCCESS] FixIt database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
