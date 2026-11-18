import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Building2, Plus, RefreshCw, School, Layers3, DoorOpen, Pencil, Trash2, X } from 'lucide-react';
import { campusService } from '../api/services';

const EMPTY_CAMPUS = { name: '', code: '' };
const EMPTY_BUILDING = { campus_id: '', name: '', code: '', total_floors: 1 };
const EMPTY_FLOOR = { building_id: '', block_id: '', floor_number: 0, floor_name: 'Ground Floor' };
const EMPTY_ROOM = { building_id: '', floor_id: '', room_number: '', room_name: '', department: '' };
const EMPTY_BLOCK = { building_id: '', name: '', code: '' };
const EMPTY_LOCATION = { campus_id: '', building_id: '', block_id: '', floor_id: '', name: '', code: '', category: 'classroom', description: '' };

export default function CampusManagementPage() {
  const [campuses, setCampuses] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [hierarchy, setHierarchy] = useState([]);
  const [customLocations, setCustomLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeForm, setActiveForm] = useState('campus');
  const [campusForm, setCampusForm] = useState(EMPTY_CAMPUS);
  const [buildingForm, setBuildingForm] = useState(EMPTY_BUILDING);
  const [floorForm, setFloorForm] = useState(EMPTY_FLOOR);
  const [roomForm, setRoomForm] = useState(EMPTY_ROOM);
  const [blockForm, setBlockForm] = useState(EMPTY_BLOCK);
  const [locationForm, setLocationForm] = useState(EMPTY_LOCATION);
  const [editing, setEditing] = useState(null);
  const [editValues, setEditValues] = useState({});

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
      setCustomLocations(hierarchyRes.data?.locations || []);
      setBuildingForm(prev => ({ ...prev, campus_id: prev.campus_id || campusRows[0]?.id || '' }));
      setFloorForm(prev => ({ ...prev, building_id: prev.building_id || buildingRows[0]?.id || '' }));
      setRoomForm(prev => ({ ...prev, building_id: prev.building_id || buildingRows[0]?.id || '' }));
      setBlockForm(prev => ({ ...prev, building_id: prev.building_id || buildingRows[0]?.id || '' }));
      setLocationForm(prev => ({ ...prev, campus_id: prev.campus_id || campusRows[0]?.id || '', building_id: prev.building_id || buildingRows[0]?.id || '' }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Campus configuration could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const selectedBuilding = useMemo(() => buildings.find(b => b.id === roomForm.building_id), [buildings, roomForm.building_id]);
  const [roomFloors, setRoomFloors] = useState([]);
  const [locationFloors, setLocationFloors] = useState([]);
  useEffect(() => {
    if (!roomForm.building_id) { setRoomFloors([]); setRoomForm(prev => ({ ...prev, floor_id: '' })); return; }
    campusService.getFloors(roomForm.building_id).then(res => {
      const rows = res.data || [];
      setRoomFloors(rows);
      setRoomForm(prev => ({ ...prev, floor_id: rows.some(f => f.id === prev.floor_id) ? prev.floor_id : (rows[0]?.id || '') }));
    }).catch(() => { setRoomFloors([]); setRoomForm(prev => ({ ...prev, floor_id: '' })); });
  }, [roomForm.building_id]);

  useEffect(() => {
    if (!locationForm.building_id) { setLocationFloors([]); return; }
    campusService.getFloors(locationForm.building_id)
      .then(res => setLocationFloors(res.data || []))
      .catch(() => setLocationFloors([]));
  }, [locationForm.building_id]);

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
      } else if (activeForm === 'room') {
        await campusService.createRoom({ ...roomForm, is_active: true, order: 0 });
        setRoomForm(prev => ({ ...EMPTY_ROOM, building_id: prev.building_id, floor_id: prev.floor_id }));
        setSuccess('Room created and linked to the selected floor.');
      } else if (activeForm === 'block') {
        await campusService.createBlock({ ...blockForm, is_active: true, order: 0 });
        setBlockForm(prev => ({ ...EMPTY_BLOCK, building_id: prev.building_id }));
        setSuccess('Block added to the selected building.');
      } else {
        await campusService.createLocation({ ...locationForm, building_id: locationForm.building_id || null, block_id: locationForm.block_id || null, floor_id: locationForm.floor_id || null, code: locationForm.code || null, is_active: true, order: 0 });
        setLocationForm(prev => ({ ...EMPTY_LOCATION, campus_id: prev.campus_id, building_id: prev.building_id }));
        setSuccess('Campus location added. Students can now select it when reporting issues.');
      }
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save campus configuration.');
    } finally {
      setSaving(false);
    }
  };


  const beginEdit = (entity, record) => {
    setEditing({ entity, id: record.id });
    setEditValues(Object.fromEntries(Object.entries(record).filter(([key, value]) =>
      !['id', '_id', 'is_active', 'rooms', 'locations', 'blocks', 'floors'].includes(key) &&
      (typeof value === 'string' || typeof value === 'number' || value === null)
    ).map(([key, value]) => [key, value ?? ''])));
    setError(''); setSuccess('');
  };
  const saveEdit = async (event) => {
    event.preventDefault();
    if (!editing) return;
    setSaving(true); setError(''); setSuccess('');
    try {
      const payload = { ...editValues };
      for (const key of ['total_floors', 'floor_number']) if (payload[key] !== undefined) payload[key] = Number(payload[key]);
      await campusService.updateStructure(editing.entity, editing.id, payload);
      setEditing(null); setEditValues({});
      setSuccess('Campus structure updated successfully.');
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update this campus structure.');
    } finally { setSaving(false); }
  };
  const deactivate = async (entity, record) => {
    if (!window.confirm('Deactivate this item? Historical records will be preserved.')) return;
    setError(''); setSuccess('');
    try {
      await campusService.deactivateStructure(entity, record.id);
      setSuccess('Item deactivated successfully.');
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not deactivate this item.');
    }
  };

  const tabs = [
    { id: 'campus', label: 'Campus', icon: School },
    { id: 'building', label: 'Building', icon: Building2 },
    { id: 'floor', label: 'Floor', icon: Layers3 },
    { id: 'room', label: 'Room', icon: DoorOpen },
    { id: 'block', label: 'Block', icon: Layers3 },
    { id: 'location', label: 'Other location', icon: DoorOpen },
  ];

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div><h1 className="page-title">Campus Configuration</h1><p className="page-subtitle">Configure campuses, buildings, blocks, floors, classrooms, hostels and any other reportable location.</p></div>
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
              <div className="form-group"><label className="form-label" htmlFor="floor-block">Block (optional)</label><select id="floor-block" className="form-control" value={floorForm.block_id} onChange={e => setFloorForm({ ...floorForm, block_id: e.target.value })}><option value="">Building-level floor</option>{(hierarchy.find(b => b.id === floorForm.building_id)?.blocks || []).map(block => <option key={block.id} value={block.id}>{block.name}</option>)}</select></div><div className="grid-2"><div className="form-group"><label className="form-label" htmlFor="floor-number">Floor number</label><input id="floor-number" className="form-control" type="number" required value={floorForm.floor_number} onChange={e => setFloorForm({ ...floorForm, floor_number: e.target.value })} /></div><div className="form-group"><label className="form-label" htmlFor="floor-name">Floor label</label><input id="floor-name" className="form-control" required value={floorForm.floor_name} onChange={e => setFloorForm({ ...floorForm, floor_name: e.target.value })} placeholder="Ground Floor" /></div></div>
            </>}
            {activeForm === 'room' && <>
              <div className="form-group"><label className="form-label" htmlFor="room-building">Building</label><select id="room-building" className="form-control" required value={roomForm.building_id} onChange={e => setRoomForm({ ...roomForm, building_id: e.target.value, floor_id: '' })}><option value="">Select building</option>{buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="room-floor">Floor</label><select id="room-floor" className="form-control" required disabled={!roomFloors.length} value={roomForm.floor_id} onChange={e => setRoomForm({ ...roomForm, floor_id: e.target.value })}><option value="">Select floor</option>{(hierarchy.find(b => b.id === locationForm.building_id)?.floors || []).map(f => <option key={f.id} value={f.id}>{f.floor_name}</option>)}</select></div>
              <div className="grid-2"><div className="form-group"><label className="form-label" htmlFor="room-number">Room number</label><input id="room-number" className="form-control" required value={roomForm.room_number} onChange={e => setRoomForm({ ...roomForm, room_number: e.target.value })} placeholder="G01" /></div><div className="form-group"><label className="form-label" htmlFor="room-name">Room name</label><input id="room-name" className="form-control" value={roomForm.room_name} onChange={e => setRoomForm({ ...roomForm, room_name: e.target.value })} placeholder="Computer Lab" /></div></div>
              <div className="form-group"><label className="form-label" htmlFor="room-department">Department (optional)</label><input id="room-department" className="form-control" value={roomForm.department} onChange={e => setRoomForm({ ...roomForm, department: e.target.value })} placeholder="Computer Science" /></div>
            </>}
            {activeForm === 'block' && <>
              <div className="form-group"><label className="form-label" htmlFor="block-building">Building</label><select id="block-building" className="form-control" required value={blockForm.building_id} onChange={e => setBlockForm({ ...blockForm, building_id: e.target.value })}><option value="">Select building</option>{buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="block-name">Block / wing name</label><input id="block-name" className="form-control" required value={blockForm.name} onChange={e => setBlockForm({ ...blockForm, name: e.target.value })} placeholder="Block A / East Wing" /></div>
              <div className="form-group"><label className="form-label" htmlFor="block-code">Block code</label><input id="block-code" className="form-control" required value={blockForm.code} onChange={e => setBlockForm({ ...blockForm, code: e.target.value.toUpperCase() })} placeholder="A" /></div>
            </>}
            {activeForm === 'location' && <>
              <div className="form-group"><label className="form-label" htmlFor="location-name">Location name</label><input id="location-name" className="form-control" required value={locationForm.name} onChange={e => setLocationForm({ ...locationForm, name: e.target.value })} placeholder="CSE Classroom 204 / Main Gate" /></div>
              <div className="form-group"><label className="form-label" htmlFor="location-category">Location category</label><select id="location-category" className="form-control" value={locationForm.category} onChange={e => setLocationForm({ ...locationForm, category: e.target.value })}>{['classroom','laboratory','hostel_room','washroom','office','library','canteen','auditorium','seminar_hall','medical_centre','sports_area','parking','gate','corridor','staircase','elevator','common_room','dining_hall','study_room','other'].map(v => <option key={v} value={v}>{v.replaceAll('_',' ').replace(/\b\w/g, c => c.toUpperCase())}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="location-campus">Campus</label><select id="location-campus" className="form-control" required value={locationForm.campus_id} onChange={e => setLocationForm({ ...locationForm, campus_id: e.target.value })}><option value="">Select campus</option>{campuses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="location-building">Building (optional for outdoor areas)</label><select id="location-building" className="form-control" value={locationForm.building_id} onChange={e => setLocationForm({ ...locationForm, building_id: e.target.value, block_id: '', floor_id: '' })}><option value="">No building / outdoor location</option>{buildings.filter(b => !locationForm.campus_id || b.campus_id === locationForm.campus_id).map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="location-block">Block / wing (optional)</label><select id="location-block" className="form-control" value={locationForm.block_id} onChange={e => setLocationForm({ ...locationForm, block_id: e.target.value })}><option value="">No specific block</option>{(hierarchy.find(b => b.id === locationForm.building_id)?.blocks || []).map(block => <option key={block.id} value={block.id}>{block.name}</option>)}</select></div>
               <div className="form-group"><label className="form-label" htmlFor="location-floor">Floor (optional)</label><select id="location-floor" className="form-control" value={locationForm.floor_id} onChange={e => setLocationForm({ ...locationForm, floor_id: e.target.value })}><option value="">No specific floor</option>{locationFloors.map(f => <option key={f.id} value={f.id}>{f.floor_name}</option>)}</select></div>
              <div className="form-group"><label className="form-label" htmlFor="location-code">Location code (optional)</label><input id="location-code" className="form-control" value={locationForm.code} onChange={e => setLocationForm({ ...locationForm, code: e.target.value.toUpperCase() })} placeholder="CLS-204" /></div>
              <div className="form-group"><label className="form-label" htmlFor="location-description">Description (optional)</label><textarea id="location-description" className="form-control" value={locationForm.description} onChange={e => setLocationForm({ ...locationForm, description: e.target.value })} placeholder="Directions or additional details" /></div>
            </>}
            <button className="btn btn-primary" type="submit" disabled={saving || (['building','location'].includes(activeForm) && !campuses.length) || (['floor','room','block'].includes(activeForm) && !buildings.length)}><Plus size={16} /> {saving ? 'Saving…' : `Add ${activeForm}`}</button>
          </form>
          {activeForm === 'building' && !campuses.length && <p className="form-error">Create a campus first.</p>}
          {['floor', 'room', 'block'].includes(activeForm) && !buildings.length && <p className="form-error">Create a building first.</p>}
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title"><Building2 size={18} /> Existing campus hierarchy</h2><span className="feature-status">{buildings.length} buildings</span></div>
          {loading ? <p style={{ color: 'var(--text-muted)' }}>Loading campus data…</p> : hierarchy.length === 0 && campuses.length === 0 && customLocations.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No campus structures configured yet. Add a campus and its buildings to activate location selection in ticket reporting.</p> : (
            <div className="campus-tree">
              {campuses.map(campus => <div className="campus-tree-building" key={campus.id}><div className="campus-tree-title"><School size={16}/><strong>{campus.name}</strong><span>{campus.code}</span><button type="button" className="btn btn-secondary" onClick={() => beginEdit('campuses', campus)} aria-label="Edit campus"><Pencil size={14}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('campuses', campus)} aria-label="Deactivate campus"><Trash2 size={14}/></button></div></div>)}
              {customLocations.filter(location => !location.building_id).length > 0 && <div className="campus-tree-building"><div className="campus-tree-title"><School size={16} /><strong>Campus-wide / Outdoor locations</strong></div>{customLocations.filter(location => !location.building_id).map(location => <div className="campus-tree-floor" key={location.id}><div><DoorOpen size={14} /> {location.name} <small>({location.category.replaceAll('_', ' ')})</small> <button type="button" className="btn btn-secondary" onClick={() => beginEdit('locations', location)}><Pencil size={13}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('locations', location)}><Trash2 size={13}/></button></div></div>)}</div>}
              {hierarchy.map(building => <div className="campus-tree-building" key={building.id}>
                <div className="campus-tree-title"><Building2 size={16} /><strong>{building.name}</strong><span>{building.code}</span><small>{campuses.find(c => c.id === building.campus_id)?.name || 'Campus'}</small><button type="button" className="btn btn-secondary" onClick={() => beginEdit('buildings', building)} aria-label="Edit building"><Pencil size={14}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('buildings', building)} aria-label="Deactivate building"><Trash2 size={14}/></button></div>
                {(building.blocks || []).map(block => <div className="campus-tree-floor" key={block.id}><div><Layers3 size={14} /> {block.name} <small>{block.code}</small> <button type="button" className="btn btn-secondary" onClick={() => beginEdit('blocks', block)}><Pencil size={13}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('blocks', block)}><Trash2 size={13}/></button></div></div>)}
                {(building.floors || []).map(floor => <div className="campus-tree-floor" key={floor.id}><div><Layers3 size={14} /> {floor.floor_name} <button type="button" className="btn btn-secondary" onClick={() => beginEdit('floors', { ...floor, building_id: building.id })}><Pencil size={13}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('floors', floor)}><Trash2 size={13}/></button></div><ul>{(floor.rooms || []).map(room => <li key={room.id}><span>{room.room_number}</span>{room.room_name && ` · ${room.room_name}`}{room.department && <small> — {room.department}</small>} <button type="button" className="btn btn-secondary" onClick={() => beginEdit('rooms', { ...room, building_id: building.id, floor_id: floor.id })}><Pencil size={13}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('rooms', room)}><Trash2 size={13}/></button></li>)}</ul></div>)}
                {customLocations.filter(location => location.building_id === building.id).map(location => <div className="campus-tree-floor" key={location.id}><div><DoorOpen size={14} /> {location.name} <small>({location.category.replaceAll('_', ' ')})</small> <button type="button" className="btn btn-secondary" onClick={() => beginEdit('locations', location)}><Pencil size={13}/></button><button type="button" className="btn btn-secondary" onClick={() => deactivate('locations', location)}><Trash2 size={13}/></button></div></div>)}
              </div>)}
            </div>
          )}
        </section>
      </div>

      {editing && <div role="dialog" aria-modal="true" aria-labelledby="campus-edit-title" className="card" style={{ position: 'fixed', top: '8%', left: '20%', right: '20%', bottom: '8%', zIndex: 1000, overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,.25)' }}>
        <div className="card-header"><h2 id="campus-edit-title">Edit campus structure</h2><button type="button" className="btn btn-secondary" onClick={() => setEditing(null)} aria-label="Close"><X size={16}/></button></div>
        <form onSubmit={saveEdit}>
          {Object.entries(editValues).map(([key, value]) => <div className="form-group" key={key}><label className="form-label">{key.replaceAll('_', ' ')}</label><input className="form-control" type={['total_floors', 'floor_number'].includes(key) ? 'number' : 'text'} value={value} onChange={event => setEditValues(prev => ({ ...prev, [key]: event.target.value }))}/></div>)}
          <div style={{ display: 'flex', gap: '.5rem', justifyContent: 'flex-end' }}><button type="button" className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button><button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</button></div>
        </form>
      </div>}
      {selectedBuilding && <span className="sr-only">Selected building: {selectedBuilding.name}</span>}
    </div>
  );
}
