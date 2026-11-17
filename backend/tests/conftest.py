import pytest
import mongomock
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.database import db_manager, MockAsyncDatabase
from app.core.security import get_password_hash, create_access_token

# Initialize test database before app import
settings.DATABASE_NAME = "test_fixit_db"
mock_client = mongomock.MongoClient()
mock_db = mock_client["test_fixit_db"]
db_manager.client = mock_client
db_manager.db = MockAsyncDatabase(mock_db)
db_manager.is_mock = True

from app.main import app

def seed_test_database():
    sync_db = mock_client["test_fixit_db"]
    users = [
        {
            "_id": "USR-TEST-ADMIN",
            "email": "test.admin@college.edu",
            "password_hash": get_password_hash("TestAdmin@123"),
            "name": "Test Admin",
            "role": "admin",
            "department": "Campus IT",
            "is_active": True,
            "specialization": ["All"]
        },
        {
            "_id": "USR-TEST-STAFF",
            "email": "test.staff@college.edu",
            "password_hash": get_password_hash("TestStaff@123"),
            "name": "Test Staff",
            "role": "staff",
            "department": "IT Support",
            "is_active": True,
            "specialization": ["Network and Wi-Fi", "Computer and Hardware"]
        },
        {
            "_id": "USR-TEST-STUDENT",
            "email": "test.student@college.edu",
            "password_hash": get_password_hash("TestStudent@123"),
            "name": "Test Student",
            "role": "student",
            "department": "Engineering",
            "is_active": True
        },
        {
            "_id": "USR-TEST-FACULTY",
            "email": "test.faculty@college.edu",
            "password_hash": get_password_hash("TestFaculty@123"),
            "name": "Test Faculty",
            "role": "faculty",
            "department": "Computer Science",
            "is_active": True
        }
    ]
    for u in users:
        sync_db.users.replace_one({"_id": u["_id"]}, u, upsert=True)

    # Campus
    sync_db.campuses.replace_one({"_id": "CAMPUS-MAIN"}, {"_id": "CAMPUS-MAIN", "name": "Main Campus", "code": "MAIN", "is_active": True}, upsert=True)

    # Buildings
    buildings = [
        {"_id": "BLD-ADM", "campus_id": "CAMPUS-MAIN", "name": "Administrative Building", "code": "ADM", "total_floors": 2, "is_active": True},
        {"_id": "BLD-ENG", "campus_id": "CAMPUS-MAIN", "name": "Engineering Block", "code": "ENG", "total_floors": 4, "is_active": True},
        {"_id": "BLD-SCI", "campus_id": "CAMPUS-MAIN", "name": "Science & Research Complex", "code": "SCI", "total_floors": 5, "is_active": True},
        {"_id": "BLD-LIB", "campus_id": "CAMPUS-MAIN", "name": "Central Library", "code": "LIB", "total_floors": 3, "is_active": True}
    ]
    for b in buildings:
        sync_db.buildings.replace_one({"_id": b["_id"]}, b, upsert=True)

    # Floors
    floors = [
        {"_id": "FLR-ADM-0", "building_id": "BLD-ADM", "floor_number": 0, "floor_name": "Ground Floor", "is_active": True},
        {"_id": "FLR-ADM-1", "building_id": "BLD-ADM", "floor_number": 1, "floor_name": "1st Floor", "is_active": True},
        {"_id": "FLR-ENG-0", "building_id": "BLD-ENG", "floor_number": 0, "floor_name": "Ground Floor", "is_active": True},
        {"_id": "FLR-ENG-1", "building_id": "BLD-ENG", "floor_number": 1, "floor_name": "1st Floor", "is_active": True},
        {"_id": "FLR-SCI-0", "building_id": "BLD-SCI", "floor_number": 0, "floor_name": "Ground Floor", "is_active": True},
        {"_id": "FLR-SCI-1", "building_id": "BLD-SCI", "floor_number": 1, "floor_name": "1st Floor", "is_active": True},
        {"_id": "FLR-SCI-2", "building_id": "BLD-SCI", "floor_number": 2, "floor_name": "2nd Floor", "is_active": True},
        {"_id": "FLR-SCI-3", "building_id": "BLD-SCI", "floor_number": 3, "floor_name": "3rd Floor", "is_active": True},
        {"_id": "FLR-SCI-4", "building_id": "BLD-SCI", "floor_number": 4, "floor_name": "4th Floor", "is_active": True}
    ]
    for f in floors:
        sync_db.floors.replace_one({"_id": f["_id"]}, f, upsert=True)

    # Rooms
    rooms = [
        {"_id": "RM-ADM-001", "building_id": "BLD-ADM", "floor_id": "FLR-ADM-0", "room_number": "101", "room_name": "Registrar Office", "department": "Administration", "is_active": True},
        {"_id": "RM-ENG-001", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-0", "room_number": "G01", "room_name": "Systems Lab", "department": "Computer Science & Engineering", "is_active": True},
        {"_id": "RM-ENG-101", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-1", "room_number": "101", "room_name": "Smart Classroom 101", "department": "Computer Science & Engineering", "is_active": True},
        {"_id": "RM-ENG-102", "building_id": "BLD-ENG", "floor_id": "FLR-ENG-1", "room_number": "Lab 102", "room_name": "Hardware Lab", "department": "Engineering", "is_active": True},
        {"_id": "RM-SCI-101", "building_id": "BLD-SCI", "floor_id": "FLR-SCI-1", "room_number": "Room 301", "room_name": "Meeting Room 301", "department": "Computer Science", "is_active": True}
    ]
    for r in rooms:
        sync_db.rooms.replace_one({"_id": r["_id"]}, r, upsert=True)

    # Legacy campus_locations for existing backward compatibility tests
    locations = [
        {"building": "Engineering Hall", "floors": ["Ground", "1st Floor", "2nd Floor"], "rooms": ["Lab 101", "Lab 102"], "is_active": True},
        {"building": "Science & Tech Block", "floors": ["Ground", "1st Floor"], "rooms": ["Computer Center B", "Room 301"], "is_active": True},
        {"building": "Central Academic Tower", "floors": ["Ground", "1st Floor", "4th Floor"], "rooms": ["Room 401"], "is_active": True}
    ]
    for loc in locations:
        sync_db.campus_locations.replace_one({"building": loc["building"]}, loc, upsert=True)

    # SLA Policies
    sla_policies = [
        {"priority": "critical", "target_resolution_hours": 2, "target_response_hours": 1},
        {"priority": "high", "target_resolution_hours": 8, "target_response_hours": 2},
        {"priority": "medium", "target_resolution_hours": 24, "target_response_hours": 4},
        {"priority": "low", "target_resolution_hours": 72, "target_response_hours": 8}
    ]
    for p in sla_policies:
        sync_db.sla_policies.replace_one({"priority": p["priority"]}, p, upsert=True)

    # Knowledge Base
    kb_articles = [
        {
            "_id": "KB-ART-001",
            "title": "How to Connect to Campus High-Speed Wi-Fi",
            "category": "Network and Wi-Fi",
            "content": "To connect your laptop to campus wifi network, select Eduroam and log in with student email.",
            "tags": ["wifi", "network"],
            "is_published": True,
            "helpful_count": 10,
            "not_helpful_count": 0
        }
    ]
    for art in kb_articles:
        sync_db.knowledge_base.replace_one({"_id": art["_id"]}, art, upsert=True)

seed_test_database()

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def ensure_db_seeded():
    seed_test_database()

@pytest.fixture
def admin_token():
    return create_access_token({"sub": "USR-TEST-ADMIN", "role": "admin"})

@pytest.fixture
def staff_token():
    return create_access_token({"sub": "USR-TEST-STAFF", "role": "staff"})

@pytest.fixture
def student_token():
    return create_access_token({"sub": "USR-TEST-STUDENT", "role": "student"})

@pytest.fixture
def faculty_token():
    return create_access_token({"sub": "USR-TEST-FACULTY", "role": "faculty"})
