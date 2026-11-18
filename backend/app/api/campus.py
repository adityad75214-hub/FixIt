import uuid
from pymongo.errors import DuplicateKeyError
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.security import get_current_user, require_roles
from app.core.audit import record_audit_log
from app.core.tenancy import institution_id_for, scoped_filter, tenant_document
from app.models.campus import (
    CampusResponse, CampusCreate,
    BuildingResponse, BuildingCreate,
    FloorResponse, FloorCreate,
    RoomResponse, RoomCreate,
    CampusHierarchyResponse, BlockCreate, BlockResponse, LocationCreate, LocationResponse
)

router = APIRouter(prefix="/campus", tags=["Campus Hierarchy"])

@router.get("", response_model=List[CampusResponse])
async def list_campuses(current_user: dict = Depends(get_current_user)):
    db = get_database()
    docs = await db.campuses.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    return [CampusResponse(id=str(d["_id"]), name=d["name"], code=d["code"], is_active=d.get("is_active", True)) for d in docs]


@router.get("/hierarchy", response_model=dict)
async def get_full_campus_hierarchy(current_user: dict = Depends(get_current_user)):
    """Returns the full active campus hierarchy: Buildings -> Floors -> Rooms."""
    db = get_database()
    buildings = await db.buildings.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    floors = await db.floors.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    rooms = await db.rooms.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    blocks = await db.blocks.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    locations = await db.campus_locations.find(scoped_filter(current_user, {"is_active": True, "location_type": "custom"})).to_list(None)

    # Nest floors into buildings and rooms into floors
    floors_by_building = {}
    for f in floors:
        b_id = f["building_id"]
        if b_id not in floors_by_building:
            floors_by_building[b_id] = []
        floors_by_building[b_id].append({
            "id": str(f["_id"]),
            "floor_name": f["floor_name"],
            "floor_number": f.get("floor_number", 0),
            "block_id": f.get("block_id"),
            "order": f.get("order", 0)
        })

    rooms_by_floor = {}
    for r in rooms:
        f_id = r["floor_id"]
        if f_id not in rooms_by_floor:
            rooms_by_floor[f_id] = []
        rooms_by_floor[f_id].append({
            "id": str(r["_id"]),
            "room_number": r["room_number"],
            "room_name": r.get("room_name"),
            "department": r.get("department"),
            "order": r.get("order", 0)
        })

    blocks_by_building = {}
    for block in blocks:
        blocks_by_building.setdefault(block["building_id"], []).append({"id": str(block["_id"]), "name": block["name"], "code": block.get("code", ""), "order": block.get("order", 0)})
    locations_by_parent = {}
    for location in locations:
        parent_id = location.get("floor_id") or location.get("block_id") or location.get("building_id") or location.get("campus_id")
        locations_by_parent.setdefault(parent_id, []).append({"id": str(location["_id"]), "name": location["name"], "code": location.get("code"), "category": location["category"], "description": location.get("description"), "order": location.get("order", 0), "building_id": location.get("building_id"), "block_id": location.get("block_id"), "floor_id": location.get("floor_id")})

    result_buildings = []
    for b in buildings:
        b_id = str(b["_id"])
        b_floors = floors_by_building.get(b_id, [])
        for bf in b_floors:
            bf["rooms"] = rooms_by_floor.get(bf["id"], [])

        result_buildings.append({
            "id": b_id,
            "name": b["name"],
            "campus_id": b.get("campus_id"),
            "code": b.get("code", ""),
            "total_floors": b.get("total_floors", len(b_floors)),
            "floors": sorted(b_floors, key=lambda x: x.get("order", 0)),
            "blocks": sorted(blocks_by_building.get(b_id, []), key=lambda x: x.get("order", 0)),
            "locations": locations_by_parent.get(b_id, [])
        })

    return {"buildings": sorted(result_buildings, key=lambda x: x.get("name", "")), "locations": [item for values in locations_by_parent.values() for item in values]}

@router.post("", response_model=CampusResponse, status_code=status.HTTP_201_CREATED)
async def create_campus(
    campus_in: CampusCreate,
    current_user: dict = Depends(require_roles("admin")),
):
    db = get_database()
    campus_id = f"CAMPUS-{uuid.uuid4().hex[:8].upper()}"
    doc = tenant_document(current_user, {"_id": campus_id, **campus_in.model_dump()})
    try:
        await db.campuses.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A campus with this code may already exist.") from None
    await record_audit_log(
        action="CAMPUS_CREATED",
        resource_type="campus",
        resource_id=campus_id,
        actor=current_user,
        details={"name": campus_in.name, "code": campus_in.code},
    )
    return CampusResponse(id=campus_id, **campus_in.model_dump())


@router.get("/buildings", response_model=List[BuildingResponse])
async def list_buildings(current_user: dict = Depends(get_current_user)):
    db = get_database()
    docs = await db.buildings.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    return [
        BuildingResponse(
            id=str(d["_id"]),
            campus_id=d.get("campus_id", "main"),
            name=d["name"],
            code=d.get("code", ""),
            total_floors=d.get("total_floors", 1),
            is_active=d.get("is_active", True),
            order=d.get("order", 0)
        )
        for d in docs
    ]

@router.post("/buildings", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    building_in: BuildingCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    campus = await db.campuses.find_one(scoped_filter(current_user, {"_id": building_in.campus_id, "is_active": True}))
    if not campus:
        raise HTTPException(status_code=400, detail="Select an existing active campus before adding a building.")
    b_id = f"BLD-{uuid.uuid4().hex[:8].upper()}"
    doc = tenant_document(current_user, {"_id": b_id, **building_in.model_dump()})
    try:
        await db.buildings.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A building with this name already exists in the selected campus.") from None
    await record_audit_log(
        action="BUILDING_CREATED",
        resource_type="building",
        resource_id=b_id,
        actor=current_user,
        details={"name": building_in.name, "floors": building_in.total_floors}
    )
    return BuildingResponse(id=b_id, **building_in.model_dump())

@router.get("/floors", response_model=List[FloorResponse])
async def list_floors(
    building_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {"is_active": True, "institution_id": institution_id_for(current_user)}
    if building_id:
        query["building_id"] = building_id
    docs = await db.floors.find(query).to_list(None)
    return [
        FloorResponse(
            id=str(d["_id"]),
            building_id=d["building_id"],
            floor_number=d.get("floor_number", 0),
            block_id=d.get("block_id"),
            floor_name=d["floor_name"],
            is_active=d.get("is_active", True),
            order=d.get("order", 0)
        )
        for d in docs
    ]

@router.post("/floors", response_model=FloorResponse, status_code=status.HTTP_201_CREATED)
async def create_floor(
    floor_in: FloorCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    building = await db.buildings.find_one(scoped_filter(current_user, {"_id": floor_in.building_id, "is_active": True}))
    if not building:
        raise HTTPException(status_code=400, detail="Select an existing active building before adding a floor.")
    if floor_in.block_id:
        block = await db.blocks.find_one(scoped_filter(current_user, {"_id": floor_in.block_id, "building_id": floor_in.building_id, "is_active": True}))
        if not block:
            raise HTTPException(status_code=400, detail="The selected block does not belong to the selected building.")
    f_id = f"FLR-{uuid.uuid4().hex[:8].upper()}"
    doc = tenant_document(current_user, {"_id": f_id, **floor_in.model_dump()})
    try:
        await db.floors.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="This floor already exists in the selected building.") from None
    await record_audit_log(action="FLOOR_CREATED", resource_type="floor", resource_id=f_id, actor=current_user, details={"building_id": floor_in.building_id, "floor_name": floor_in.floor_name})
    return FloorResponse(id=f_id, **floor_in.model_dump())

@router.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    floor_id: Optional[str] = None,
    building_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {"is_active": True, "institution_id": institution_id_for(current_user)}
    if floor_id:
        query["floor_id"] = floor_id
    if building_id:
        query["building_id"] = building_id
    docs = await db.rooms.find(query).to_list(None)
    return [
        RoomResponse(
            id=str(d["_id"]),
            floor_id=d["floor_id"],
            building_id=d["building_id"],
            room_number=d["room_number"],
            room_name=d.get("room_name"),
            department=d.get("department"),
            is_active=d.get("is_active", True),
            order=d.get("order", 0)
        )
        for d in docs
    ]

@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_in: RoomCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    floor = await db.floors.find_one(scoped_filter(current_user, {"_id": room_in.floor_id, "building_id": room_in.building_id, "is_active": True}))
    if not floor:
        raise HTTPException(status_code=400, detail="The selected floor does not belong to the selected building.")
    r_id = f"RM-{uuid.uuid4().hex[:8].upper()}"
    doc = tenant_document(current_user, {"_id": r_id, **room_in.model_dump()})
    try:
        await db.rooms.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="This room number already exists on the selected floor.") from None
    await record_audit_log(action="ROOM_CREATED", resource_type="room", resource_id=r_id, actor=current_user, details={"building_id": room_in.building_id, "floor_id": room_in.floor_id, "room_number": room_in.room_number})
    return RoomResponse(id=r_id, **room_in.model_dump())



@router.get("/blocks", response_model=List[BlockResponse])
async def list_blocks(building_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = get_database()
    query = {"is_active": True, "institution_id": institution_id_for(current_user)}
    if building_id:
        query["building_id"] = building_id
    docs = await db.blocks.find(query).sort("order", 1).to_list(None)
    return [BlockResponse(id=str(d["_id"]), **{k: v for k, v in d.items() if k != "_id"}) for d in docs]


@router.post("/blocks", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(block_in: BlockCreate, current_user: dict = Depends(require_roles("admin"))):
    db = get_database()
    building = await db.buildings.find_one(scoped_filter(current_user, {"_id": block_in.building_id, "is_active": True}))
    if not building:
        raise HTTPException(status_code=400, detail="Select an existing active building.")
    block_id = f"BLK-{uuid.uuid4().hex[:8].upper()}"
    doc = tenant_document(current_user, {"_id": block_id, **block_in.model_dump()})
    try:
        await db.blocks.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A block with this code may already exist in the building.") from None
    await record_audit_log(action="BLOCK_CREATED", resource_type="block", resource_id=block_id, actor=current_user, details={"building_id": block_in.building_id, "name": block_in.name})
    return BlockResponse(id=block_id, **block_in.model_dump())


@router.get("/locations", response_model=List[LocationResponse])
async def list_custom_locations(campus_id: Optional[str] = None, building_id: Optional[str] = None, block_id: Optional[str] = None, floor_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    db = get_database()
    query = {"is_active": True, "location_type": "custom"}
    for key, value in (("campus_id", campus_id), ("building_id", building_id), ("block_id", block_id), ("floor_id", floor_id)):
        if value:
            query[key] = value
    docs = await db.campus_locations.find(scoped_filter(current_user, query)).sort("order", 1).to_list(None)
    return [LocationResponse(id=str(d["_id"]), **{k: v for k, v in d.items() if k not in ("_id", "location_type")}) for d in docs]


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_location(location_in: LocationCreate, current_user: dict = Depends(require_roles("admin"))):
    db = get_database()
    campus = await db.campuses.find_one(scoped_filter(current_user, {"_id": location_in.campus_id, "is_active": True}))
    if not campus:
        raise HTTPException(status_code=400, detail="Select an existing active campus.")
    if location_in.building_id:
        building = await db.buildings.find_one(scoped_filter(current_user, {"_id": location_in.building_id, "campus_id": location_in.campus_id, "is_active": True}))
        if not building:
            raise HTTPException(status_code=400, detail="The building does not belong to the selected campus.")
    if location_in.block_id:
        block = await db.blocks.find_one(scoped_filter(current_user, {"_id": location_in.block_id, "building_id": location_in.building_id, "is_active": True}))
        if not block:
            raise HTTPException(status_code=400, detail="The block does not belong to the selected building.")
    if location_in.floor_id:
        floor = await db.floors.find_one(scoped_filter(current_user, {"_id": location_in.floor_id, "building_id": location_in.building_id, "is_active": True}))
        if not floor:
            raise HTTPException(status_code=400, detail="The floor does not belong to the selected building.")
    location_id = f"LOC-{uuid.uuid4().hex[:8].upper()}"
    doc = tenant_document(current_user, {"_id": location_id, **location_in.model_dump(), "location_type": "custom"})
    try:
        await db.campus_locations.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="A location with this code may already exist.") from None
    await record_audit_log(action="LOCATION_CREATED", resource_type="campus_location", resource_id=location_id, actor=current_user, details={"name": location_in.name, "category": location_in.category, "campus_id": location_in.campus_id})
    return LocationResponse(id=location_id, **location_in.model_dump())


# Administrative maintenance endpoints. Records are deactivated, never physically
# removed, so historical ticket references and audit trails remain intact.
from datetime import datetime, timezone
from fastapi import Body
import re

# Parent IDs are deliberately immutable through this endpoint. This prevents an
# ordinary edit from silently moving existing hierarchy records between parents.
_CAMPUS_ENTITIES = {
    "campuses": ("campuses", {"name", "code"}),
    "buildings": ("buildings", {"name", "code", "total_floors", "order"}),
    "floors": ("floors", {"floor_number", "floor_name", "order"}),
    "rooms": ("rooms", {"room_number", "room_name", "department", "order"}),
    "blocks": ("blocks", {"name", "code", "order"}),
    "locations": ("campus_locations", {"name", "code", "category", "description", "order"}),
}

async def _validate_campus_parent(db, user, entity, values):
    if entity == "buildings":
        parent = await db.campuses.find_one(scoped_filter(user, {"_id": values.get("campus_id"), "is_active": True}))
        if not parent:
            raise HTTPException(status_code=400, detail="Select an active campus.")
    elif entity in ("floors", "rooms", "blocks"):
        building = await db.buildings.find_one(scoped_filter(user, {"_id": values.get("building_id"), "is_active": True}))
        if not building:
            raise HTTPException(status_code=400, detail="Select an active building.")
        if entity == "rooms":
            floor = await db.floors.find_one(scoped_filter(user, {"_id": values.get("floor_id"), "building_id": values.get("building_id"), "is_active": True}))
            if not floor:
                raise HTTPException(status_code=400, detail="The selected floor does not belong to this building.")
        if entity == "floors" and values.get("block_id"):
            block = await db.blocks.find_one(scoped_filter(user, {"_id": values["block_id"], "building_id": values.get("building_id"), "is_active": True}))
            if not block:
                raise HTTPException(status_code=400, detail="The selected block does not belong to this building.")
    elif entity == "locations":
        campus = await db.campuses.find_one(scoped_filter(user, {"_id": values.get("campus_id"), "is_active": True}))
        if not campus:
            raise HTTPException(status_code=400, detail="Select an active campus.")
        if values.get("building_id"):
            building = await db.buildings.find_one(scoped_filter(user, {"_id": values["building_id"], "campus_id": values["campus_id"], "is_active": True}))
            if not building:
                raise HTTPException(status_code=400, detail="The building does not belong to the selected campus.")
        if values.get("block_id"):
            block = await db.blocks.find_one(scoped_filter(user, {"_id": values["block_id"], "building_id": values.get("building_id"), "is_active": True}))
            if not block:
                raise HTTPException(status_code=400, detail="The block does not belong to the selected building.")
        if values.get("floor_id"):
            floor = await db.floors.find_one(scoped_filter(user, {"_id": values["floor_id"], "building_id": values.get("building_id"), "is_active": True}))
            if not floor:
                raise HTTPException(status_code=400, detail="The floor does not belong to the selected building.")

def _ticket_text_match(value: str) -> dict:
    return {"$regex": f"^{re.escape(value.strip())}$", "$options": "i"}

@router.put("/{entity}/{record_id}")
async def update_campus_structure(entity: str, record_id: str, payload: dict = Body(...), current_user: dict = Depends(require_roles("admin"))):
    if entity not in _CAMPUS_ENTITIES:
        raise HTTPException(status_code=404, detail="Unknown campus structure type.")
    collection_name, allowed = _CAMPUS_ENTITIES[entity]
    unknown = set(payload) - allowed
    if unknown:
        raise HTTPException(status_code=400, detail="Parent links and system fields cannot be edited here. Change only the displayed details.")
    values = dict(payload)
    if not values:
        raise HTTPException(status_code=400, detail="No editable fields were supplied.")
    required_text = {
        "name", "code", "floor_name", "room_number", "category"
    }
    for key, value in values.items():
        if key in required_text:
            if not isinstance(value, str) or not value.strip():
                raise HTTPException(status_code=422, detail=f"{key} cannot be empty.")
            values[key] = value.strip()
    for key in ("total_floors", "floor_number", "order"):
        if key in values:
            try:
                values[key] = int(values[key])
            except (TypeError, ValueError):
                raise HTTPException(status_code=422, detail=f"{key} must be a whole number.") from None
    if "total_floors" in values and not 1 <= values["total_floors"] <= 100:
        raise HTTPException(status_code=422, detail="Number of floors must be between 1 and 100.")
    if "floor_number" in values and not -10 <= values["floor_number"] <= 200:
        raise HTTPException(status_code=422, detail="Floor number must be between -10 and 200.")
    db = get_database()
    collection = getattr(db, collection_name)
    current = await collection.find_one(scoped_filter(current_user, {"_id": record_id, "is_active": True}))
    if not current:
        raise HTTPException(status_code=404, detail="Active campus structure not found.")
    merged = {**current, **values}
    await _validate_campus_parent(db, current_user, entity, merged)
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        result = await collection.update_one(scoped_filter(current_user, {"_id": record_id, "is_active": True}), {"$set": values})
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An active campus item with the same unique code or name already exists.") from None
    if not result.matched_count:
        raise HTTPException(status_code=409, detail="This record changed. Refresh and try again.")
    await record_audit_log(action=f"{entity[:-1].upper()}_UPDATED", resource_type=entity[:-1], resource_id=record_id, actor=current_user, details={"changed_fields": sorted(values.keys())})
    updated = await collection.find_one(scoped_filter(current_user, {"_id": record_id}))
    return {key: value for key, value in updated.items() if key != "_id"} | {"id": record_id}

@router.delete("/{entity}/{record_id}")
async def deactivate_campus_structure(entity: str, record_id: str, current_user: dict = Depends(require_roles("admin"))):
    if entity not in _CAMPUS_ENTITIES:
        raise HTTPException(status_code=404, detail="Unknown campus structure type.")
    collection_name, _ = _CAMPUS_ENTITIES[entity]
    db = get_database()
    collection = getattr(db, collection_name)
    current = await collection.find_one(scoped_filter(current_user, {"_id": record_id, "is_active": True}))
    if not current:
        raise HTTPException(status_code=404, detail="Active campus structure not found.")

    # Do not deactivate a parent while active child records still depend on it.
    child_dependencies = {
        "campuses": [("buildings", {"campus_id": record_id}), ("campus_locations", {"campus_id": record_id})],
        "buildings": [("floors", {"building_id": record_id}), ("blocks", {"building_id": record_id}), ("rooms", {"building_id": record_id}), ("campus_locations", {"building_id": record_id})],
        "floors": [("rooms", {"floor_id": record_id}), ("campus_locations", {"floor_id": record_id})],
        "blocks": [("floors", {"block_id": record_id}), ("campus_locations", {"block_id": record_id})],
    }
    for dependency_collection, query in child_dependencies.get(entity, []):
        count = await getattr(db, dependency_collection).count_documents(scoped_filter(current_user, {**query, "is_active": True}))
        if count:
            raise HTTPException(status_code=409, detail=f"Cannot deactivate this item because {count} active dependent {dependency_collection} record(s) exist. Deactivate or move them first.")

    # Tickets store human-readable building/floor/room values (not room_id or
    # location_id). Check those real fields so historical ticket locations remain valid.
    ticket_query = None
    if entity == "campuses":
        ticket_query = {"campus_id": record_id}
    elif entity == "buildings":
        campus = await db.campuses.find_one(scoped_filter(current_user, {"_id": current.get("campus_id")}))
        ticket_query = {"campus_id": current.get("campus_id"), "building": _ticket_text_match(current.get("name", ""))}
    elif entity == "floors":
        building = await db.buildings.find_one(scoped_filter(current_user, {"_id": current.get("building_id")}))
        ticket_query = {"building": _ticket_text_match((building or {}).get("name", "")), "floor": _ticket_text_match(current.get("floor_name", ""))}
        if building and building.get("campus_id"):
            ticket_query["campus_id"] = building["campus_id"]
    elif entity == "rooms":
        building = await db.buildings.find_one(scoped_filter(current_user, {"_id": current.get("building_id")}))
        floor = await db.floors.find_one(scoped_filter(current_user, {"_id": current.get("floor_id")}))
        ticket_query = {
            "building": _ticket_text_match((building or {}).get("name", "")),
            "floor": _ticket_text_match((floor or {}).get("floor_name", "")),
            "$or": [
                {"room": _ticket_text_match(current.get("room_number", ""))},
                {"room": _ticket_text_match(current.get("room_name", ""))},
            ],
        }
        if building and building.get("campus_id"):
            ticket_query["campus_id"] = building["campus_id"]
    elif entity == "locations":
        building = await db.buildings.find_one(scoped_filter(current_user, {"_id": current.get("building_id")})) if current.get("building_id") else None
        floor = await db.floors.find_one(scoped_filter(current_user, {"_id": current.get("floor_id")})) if current.get("floor_id") else None
        ticket_query = {"campus_id": current.get("campus_id"), "room": _ticket_text_match(current.get("name", ""))}
        if building:
            ticket_query["building"] = _ticket_text_match(building.get("name", ""))
        else:
            ticket_query["building"] = {"$in": ["Campus-wide / Outdoor", "Campus grounds", "Outdoor"]}
        if floor:
            ticket_query["floor"] = _ticket_text_match(floor.get("floor_name", ""))
    if ticket_query:
        ticket_count = await db.tickets.count_documents(scoped_filter(current_user, ticket_query))
        if ticket_count:
            raise HTTPException(status_code=409, detail=f"Cannot deactivate this item because {ticket_count} ticket(s) reference its location. Keep it active to preserve ticket history.")

    now = datetime.now(timezone.utc).isoformat()
    result = await collection.update_one(scoped_filter(current_user, {"_id": record_id, "is_active": True}), {"$set": {"is_active": False, "deactivated_at": now, "updated_at": now}})
    if not result.matched_count:
        raise HTTPException(status_code=409, detail="This record changed. Refresh and try again.")
    await record_audit_log(action=f"{entity[:-1].upper()}_DEACTIVATED", resource_type=entity[:-1], resource_id=record_id, actor=current_user, details={"name": current.get("name") or current.get("floor_name") or current.get("room_number")})
    return {"message": "Campus structure deactivated. Historical records were preserved.", "id": record_id}
