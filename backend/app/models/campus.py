from typing import Optional, List
from pydantic import BaseModel, Field

class CampusBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    is_active: bool = True

class CampusCreate(CampusBase):
    pass

class CampusResponse(CampusBase):
    id: str

class BuildingBase(BaseModel):
    campus_id: str = Field(..., min_length=1, max_length=80)
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    total_floors: int = Field(default=1, ge=1, le=100)
    is_active: bool = True
    order: int = 0

class BuildingCreate(BuildingBase):
    pass

class BuildingResponse(BuildingBase):
    id: str

class FloorBase(BaseModel):
    building_id: str = Field(..., min_length=1, max_length=80)
    floor_number: int = Field(..., ge=-10, le=200)
    floor_name: str = Field(..., min_length=1, max_length=60)
    is_active: bool = True
    order: int = 0

class FloorCreate(FloorBase):
    pass

class FloorResponse(FloorBase):
    id: str

class RoomBase(BaseModel):
    floor_id: str = Field(..., min_length=1, max_length=80)
    building_id: str = Field(..., min_length=1, max_length=80)
    room_number: str = Field(..., min_length=1, max_length=40)
    room_name: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = True
    order: int = 0

class RoomCreate(RoomBase):
    pass

class RoomResponse(RoomBase):
    id: str

class CampusHierarchyResponse(BaseModel):
    buildings: List[dict]


class BlockBase(BaseModel):
    building_id: str = Field(..., min_length=1, max_length=80)
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    is_active: bool = True
    order: int = 0

class BlockCreate(BlockBase):
    pass

class BlockResponse(BlockBase):
    id: str

class LocationBase(BaseModel):
    campus_id: str = Field(..., min_length=1, max_length=80)
    building_id: Optional[str] = Field(default=None, max_length=80)
    block_id: Optional[str] = Field(default=None, max_length=80)
    floor_id: Optional[str] = Field(default=None, max_length=80)
    name: str = Field(..., min_length=2, max_length=120)
    code: Optional[str] = Field(default=None, max_length=40)
    category: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = True
    order: int = 0

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: str
