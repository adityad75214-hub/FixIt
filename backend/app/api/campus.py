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
    query = {"is_active": True}
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
    query = {"is_active": True}
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
