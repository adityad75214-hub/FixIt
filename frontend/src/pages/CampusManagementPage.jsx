import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Building2, Plus, RefreshCw, School, Layers3, DoorOpen } from 'lucide-react';
import { campusService } from '../api/services';

const EMPTY_CAMPUS = { name: '', code: '' };
const EMPTY_BUILDING = { campus_id: '', name: '', code: '', total_floors: 1 };
const EMPTY_FLOOR = { building_id: '', floor_number: 0, floor_name: 'Ground Floor' };
const EMPTY_ROOM = { building_id: '', floor_id: '', room_number: '', room_name: '', department: '' };

export default function CampusManagementPage() {
  const [campuses, setCampuses] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [hierarchy, setHierarchy] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeForm, setActiveForm] = useState('campus');
  const [campusForm, setCampusForm] = useState(EMPTY_CAMPUS);
  const [buildingForm, setBuildingForm] = useState(EMPTY_BUILDING);
  const [floorForm, setFloorForm] = useState(EMPTY_FLOOR);
  const [roomForm, setRoomForm] = useState(EMPTY_ROOM);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [campusRes, buildingRes, hierarchyRes] = await Promise.all([
        campusService.getCampuses(), campusService.getBuildings(), campusService.getHierarchy()
      ]);
      const campusRows = campusRes.data || [];
      const buildingRows = buildingRes.data || [];
      setCampuses(campusRows);
      setBuildings(buildingRows);
      setHierarchy(hierarchyRes.data?.buildings || []);
      setBuildingForm(prev => ({ ...prev, campus_id: prev.campus_id || campusRows[0]?.id || '' }));
      setFloorForm(prev => ({ ...prev, building_id: prev.building_id || buildingRows[0]?.id || '' }));
      setRoomForm(prev => ({ ...prev, building_id: prev.building_id || buildingRows[0]?.id || '' }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Campus configuration could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const selectedBuilding = useMemo(() => buildings.find(b => b.id === roomForm.building_id), [buildings, roomForm.building_id]);
  const [roomFloors, setRoomFloors] = useState([]);
  useEffect(() => {
    if (!roomForm.building_id) { setRoomFloors([]); setRoomForm(prev => ({ ...prev, floor_id: '' })); return; }
    campusService.getFloors(roomForm.building_id).then(res => {
      const rows = res.data || [];
      setRoomFloors(rows);
      setRoomForm(prev => ({ ...prev, floor_id: rows.some(f => f.id === prev.floor_id) ? prev.floor_id : (rows[0]?.id || '') }));
    }).catch(() => { setRoomFloors([]); setRoomForm(prev => ({ ...prev, floor_id: '' })); });
  }, [roomForm.building_id]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true); setError(''); setSuccess('');
    try {
      if (activeForm === 'campus') {
        await campusService.createCampus({ ...campusForm, is_active: true });
        setCampusForm(EMPTY_CAMPUS);
        setSuccess('Campus created. You can now add buildings.');
        setActiveForm('building');
      } else if (activeForm === 'building') {
        await campusService.createBuilding({ ...buildingForm, total_floors: Number(buildingForm.total_floors), is_active: true, order: 0 });
        setBuildingForm(prev => ({ ...EMPTY_BUILDING, campus_id: prev.campus_id }));
        setSuccess('Building created. Add its floors next.');
        setActiveForm('floor');
      } else if (activeForm === 'floor') {
        await campusService.createFloor({ ...floorForm, floor_number: Number(floorForm.floor_number), is_active: true, order: Number(floorForm.floor_number) });
        setFloorForm(prev => ({ ...EMPTY_FLOOR, building_id: prev.building_id }));
        setSuccess('Floor created. You can now add rooms.');
        setActiveForm('room');
      } else {
        await campusService.createRoom({ ...roomForm, is_active: true, order: 0 });
        setRoomForm(prev => ({ ...EMPTY_ROOM, building_id: prev.building_id, floor_id: prev.floor_id }));
        setSuccess('Room created and linked to the selected floor.');
      }
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save campus configuration.');
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'campus', label: 'Campus', icon: School },
    { id: 'building', label: 'Building', icon: Building2 },
    { id: 'floor', label: 'Floor', icon: Layers3 },
    { id: 'room', label: 'Room', icon: DoorOpen },
  ];

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div><h1 className="page-title">Campus Configuration</h1><p className="page-subtitle">Manage the real campus → building → floor → room hierarchy used by ticket reporting.</p></div>
        <button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw size={16} /> Refresh</button>
      </div>

      {error && <div className="card" role="alert" style={{ color: '#b91c1c', borderColor: '#fca5a5', marginBottom: '1rem' }}>{error}</div>}
      {success && <div className="card" role="status" style={{ color: '#047857', borderColor: '#86efac', marginBottom: '1rem' }}>{success}</div>}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <section className="card">
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Add campus structure</h2>
          <div className="campus-tabs" role="tablist" aria-label="Campus entity type">
            {tabs.map(tab => { const Icon = tab.icon; return <button key={tab.id} type="button" role="tab" aria-selected={activeForm === tab.id} className={`campus-tab ${activeForm === tab.id ? 'active' : ''}`} onClick={() => setActiveForm(tab.id)}><Icon size={15} /> {tab.label}</button>; })}
          </div>
          <form onSubmit={submit}>
            {activeForm === 'campus' && <>
              <div className="form-group"><label className="form-label" htmlFor="campus-name">Campus name</label><input id="campus-name" className="form-control" required minLength={2} maxLength={100} value={campusForm.name} onChange={e => setCampusForm({ ...campusForm, name: e.target.value })} placeholder="Main Campus" /></div>
              <div className="form-group"><label className="form-label" htmlFor="campus-code">Campus code</label><input id="campus-code" className="form-control" required minLength={2} maxLength={20} value={campusForm.code} onChange={e => setCampusForm({ ...campusForm, code: e.target.value.toUpperCase() })} placeholder="MAIN" /></div>
            </>}
            {activeForm === 'building' && <>
              <div className="form-group"><label className="form-label" htmlFor="building-campus">Campus</label><select id="building-campus" className="form-control" required value={buildingForm.campus_id} onChange={e => setBuildingForm({ ...buildingForm, campus_id: e.target.value })}><option value="">Select campus</option>{campuses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="building-name">Building name</label><input id="building-name" className="form-control" required minLength={2} value={buildingForm.name} onChange={e => setBuildingForm({ ...buildingForm, name: e.target.value })} placeholder="Engineering Block" /></div>
              <div className="grid-2"><div className="form-group"><label className="form-label" htmlFor="building-code">Code</label><input id="building-code" className="form-control" required value={buildingForm.code} onChange={e => setBuildingForm({ ...buildingForm, code: e.target.value.toUpperCase() })} placeholder="ENG" /></div><div className="form-group"><label className="form-label" htmlFor="building-floors">Number of floors</label><input id="building-floors" className="form-control" type="number" min="1" max="100" required value={buildingForm.total_floors} onChange={e => setBuildingForm({ ...buildingForm, total_floors: e.target.value })} /></div></div>
            </>}
            {activeForm === 'floor' && <>
              <div className="form-group"><label className="form-label" htmlFor="floor-building">Building</label><select id="floor-building" className="form-control" required value={floorForm.building_id} onChange={e => setFloorForm({ ...floorForm, building_id: e.target.value })}><option value="">Select building</option>{buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></div>
              <div className="grid-2"><div className="form-group"><label className="form-label" htmlFor="floor-number">Floor number</label><input id="floor-number" className="form-control" type="number" required value={floorForm.floor_number} onChange={e => setFloorForm({ ...floorForm, floor_number: e.target.value })} /></div><div className="form-group"><label className="form-label" htmlFor="floor-name">Floor label</label><input id="floor-name" className="form-control" required value={floorForm.floor_name} onChange={e => setFloorForm({ ...floorForm, floor_name: e.target.value })} placeholder="Ground Floor" /></div></div>
            </>}
            {activeForm === 'room' && <>
              <div className="form-group"><label className="form-label" htmlFor="room-building">Building</label><select id="room-building" className="form-control" required value={roomForm.building_id} onChange={e => setRoomForm({ ...roomForm, building_id: e.target.value, floor_id: '' })}><option value="">Select building</option>{buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="room-floor">Floor</label><select id="room-floor" className="form-control" required disabled={!roomFloors.length} value={roomForm.floor_id} onChange={e => setRoomForm({ ...roomForm, floor_id: e.target.value })}><option value="">Select floor</option>{roomFloors.map(f => <option key={f.id} value={f.id}>{f.floor_name}</option>)}</select></div>
              <div className="grid-2"><div className="form-group"><label className="form-label" htmlFor="room-number">Room number</label><input id="room-number" className="form-control" required value={roomForm.room_number} onChange={e => setRoomForm({ ...roomForm, room_number: e.target.value })} placeholder="G01" /></div><div className="form-group"><label className="form-label" htmlFor="room-name">Room name</label><input id="room-name" className="form-control" value={roomForm.room_name} onChange={e => setRoomForm({ ...roomForm, room_name: e.target.value })} placeholder="Computer Lab" /></div></div>
              <div className="form-group"><label className="form-label" htmlFor="room-department">Department (optional)</label><input id="room-department" className="form-control" value={roomForm.department} onChange={e => setRoomForm({ ...roomForm, department: e.target.value })} placeholder="Computer Science" /></div>
            </>}
            <button className="btn btn-primary" type="submit" disabled={saving || (activeForm === 'building' && !campuses.length) || (['floor', 'room'].includes(activeForm) && !buildings.length)}><Plus size={16} /> {saving ? 'Saving…' : `Add ${activeForm}`}</button>
          </form>
          {activeForm === 'building' && !campuses.length && <p className="form-error">Create a campus first.</p>}
          {['floor', 'room'].includes(activeForm) && !buildings.length && <p className="form-error">Create a building first.</p>}
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title"><Building2 size={18} /> Existing campus hierarchy</h2><span className="feature-status">{buildings.length} buildings</span></div>
          {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading campus data…</p> : hierarchy.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No buildings configured yet. Add a campus and its buildings to activate location selection in ticket reporting.</p> : (
            <div className="campus-tree">
              {hierarchy.map(building => <div className="campus-tree-building" key={building.id}>
                <div className="campus-tree-title"><Building2 size={16} /><strong>{building.name}</strong><span>{building.code}</span></div>
                {(building.floors || []).map(floor => <div className="campus-tree-floor" key={floor.id}><div><Layers3 size={14} /> {floor.floor_name}</div><ul>{(floor.rooms || []).map(room => <li key={room.id}><span>{room.room_number}</span>{room.room_name && ` · ${room.room_name}`}{room.department && <small> — {room.department}</small>}</li>)}</ul></div>)}
              </div>)}
            </div>
          )}
        </section>
      </div>
      {selectedBuilding && <span className="sr-only">Selected building: {selectedBuilding.name}</span>}
    </div>
  );
}
