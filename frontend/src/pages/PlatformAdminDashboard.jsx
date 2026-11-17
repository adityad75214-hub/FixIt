import React, { useEffect, useState } from 'react';
import { Building2, Plus, RefreshCw, ShieldCheck, Users } from 'lucide-react';
import { institutionService } from '../api/services';

const emptyInstitution = { name: '', slug: '', email_domains: '' };
const emptyAdmin = { email: '', name: '', password: '' };
const emptyEdit = { name: '', email_domains: '' };

export default function PlatformAdminDashboard() {
  const [institutions, setInstitutions] = useState([]);
  const [institutionForm, setInstitutionForm] = useState(emptyInstitution);
  const [adminForm, setAdminForm] = useState(emptyAdmin);
  const [editForm, setEditForm] = useState(emptyEdit);
  const [selectedInstitution, setSelectedInstitution] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadInstitutions = async () => {
    setLoading(true);
    try {
      const response = await institutionService.manageList();
      const rows = response.data || [];
      setInstitutions(rows);
      setSelectedInstitution((current) => current && rows.some((item) => item.id === current && item.status === 'active') ? current : (rows.find((item) => item.status === 'active')?.id || ''));
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load institution workspaces.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadInstitutions(); }, []);

  const createInstitution = async (event) => {
    event.preventDefault();
    setSaving(true); setError(''); setNotice('');
    try {
      const payload = {
        name: institutionForm.name.trim(),
        slug: institutionForm.slug.trim().toLowerCase(),
        email_domains: institutionForm.email_domains.split(',').map((value) => value.trim().toLowerCase().replace(/^@/, '')).filter(Boolean),
      };
      const response = await institutionService.create(payload);
      setInstitutionForm(emptyInstitution);
      setNotice(`Workspace "${response.data.name}" created. Provision its first college administrator below.`);
      await loadInstitutions();
      setSelectedInstitution(response.data.id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Institution could not be created.');
    } finally { setSaving(false); }
  };

  const createAdmin = async (event) => {
    event.preventDefault();
    if (!selectedInstitution) return;
    setSaving(true); setError(''); setNotice('');
    try {
      const response = await institutionService.createAdmin(selectedInstitution, adminForm);
      setAdminForm(emptyAdmin);
      setNotice(`College administrator account created for ${response.data.email}. Share the temporary password securely and ask them to change it immediately.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Administrator account could not be created.');
    } finally { setSaving(false); }
  };

  const toggleInstitutionStatus = async (institution) => {
    const nextStatus = institution.status === 'active' ? 'suspended' : 'active';
    setSaving(true); setError(''); setNotice('');
    try {
      await institutionService.update(institution.id, { status: nextStatus });
      setNotice(`${institution.name} workspace is now ${nextStatus}.`);
      await loadInstitutions();
    } catch (err) {
      setError(err.response?.data?.detail || 'Workspace status could not be updated.');
    } finally { setSaving(false); }
  };

  const selected = institutions.find((item) => item.id === selectedInstitution);

  useEffect(() => {
    if (selected) setEditForm({ name: selected.name, email_domains: (selected.email_domains || []).join(', ') });
    else setEditForm(emptyEdit);
  }, [selectedInstitution, institutions]);

  const updateInstitutionDetails = async (event) => {
    event.preventDefault();
    if (!selected) return;
    setSaving(true); setError(''); setNotice('');
    try {
      const payload = {
        name: editForm.name.trim(),
        email_domains: editForm.email_domains.split(',').map((value) => value.trim().toLowerCase().replace(/^@/, '')).filter(Boolean),
      };
      const response = await institutionService.update(selected.id, payload);
      setNotice(`Workspace details for ${response.data.name} updated.`);
      await loadInstitutions();
    } catch (err) {
      setError(err.response?.data?.detail || 'Workspace details could not be updated.');
    } finally { setSaving(false); }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">FixIt Platform Operations</h1>
          <p className="page-subtitle">Register colleges, manage workspaces and provision their first administrator.</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={loadInstitutions} disabled={loading}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {error && <div className="form-error" role="alert" style={{ marginBottom: '1rem' }}>{error}</div>}
      {notice && <div className="card" role="status" style={{ marginBottom: '1rem' }}>{notice}</div>}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <section className="card">
          <div className="card-header"><h2 className="card-title"><Building2 size={18} /> Create institution workspace</h2></div>
          <form onSubmit={createInstitution}>
            <div className="form-group">
              <label className="form-label" htmlFor="institution-name">College / institution name</label>
              <input id="institution-name" className="form-control" required minLength={2} maxLength={160} value={institutionForm.name} onChange={(e) => setInstitutionForm({ ...institutionForm, name: e.target.value })} placeholder="National Institute of Engineering" />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="institution-slug">Workspace slug</label>
              <input id="institution-slug" className="form-control" required pattern="[a-z0-9]+(?:-[a-z0-9]+)*" value={institutionForm.slug} onChange={(e) => setInstitutionForm({ ...institutionForm, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') })} placeholder="nie-mysuru" />
              <small>Used by the college selector and future workspace URLs.</small>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="institution-domains">Approved email domains</label>
              <input id="institution-domains" className="form-control" value={institutionForm.email_domains} onChange={(e) => setInstitutionForm({ ...institutionForm, email_domains: e.target.value })} placeholder="nie.ac.in, students.nie.ac.in" />
              <small>Comma-separated. Domain matching is not email ownership verification.</small>
            </div>
            <button className="btn btn-primary" type="submit" disabled={saving}><Plus size={16} /> {saving ? 'Creating…' : 'Create workspace'}</button>
          </form>
        </section>

        <section className="card">
          <div className="card-header"><h2 className="card-title"><ShieldCheck size={18} /> Provision college administrator</h2></div>
          <form onSubmit={createAdmin}>
            <div className="form-group">
              <label className="form-label" htmlFor="admin-institution">Institution workspace</label>
              <select id="admin-institution" className="form-control" value={selectedInstitution} onChange={(e) => setSelectedInstitution(e.target.value)} required>
                <option value="">Select an institution</option>
                {institutions.filter((item) => item.status === 'active').map((item) => <option key={item.id} value={item.id}>{item.name} ({item.slug})</option>)}
              </select>
            </div>
            {selected && <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Administrator will have access only to <strong>{selected.name}</strong>.</p>}
            <div className="form-group">
              <label className="form-label" htmlFor="admin-name">Administrator name</label>
              <input id="admin-name" className="form-control" required minLength={2} maxLength={120} value={adminForm.name} onChange={(e) => setAdminForm({ ...adminForm, name: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="admin-email">Official college email</label>
              <input id="admin-email" type="email" className="form-control" required value={adminForm.email} onChange={(e) => setAdminForm({ ...adminForm, email: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="admin-password">Temporary password</label>
              <input id="admin-password" type="password" className="form-control" required minLength={12} maxLength={128} value={adminForm.password} onChange={(e) => setAdminForm({ ...adminForm, password: e.target.value })} autoComplete="new-password" />
            </div>
            <button className="btn btn-primary" type="submit" disabled={saving || !selectedInstitution}><Users size={16} /> {saving ? 'Provisioning…' : 'Create college admin'}</button>
          </form>
        </section>
      </div>

      <section className="card" style={{ marginTop: '1.25rem' }}>
        <div className="card-header"><h2 className="card-title"><Building2 size={18} /> Edit selected workspace</h2></div>
        {!selected ? <p>Select an active workspace to edit its details.</p> : (
          <form onSubmit={updateInstitutionDetails}>
            <div className="form-group">
              <label className="form-label" htmlFor="edit-institution-name">Institution name</label>
              <input id="edit-institution-name" className="form-control" required minLength={2} maxLength={160} value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="edit-institution-domains">Approved email domains</label>
              <input id="edit-institution-domains" className="form-control" value={editForm.email_domains} onChange={(e) => setEditForm({ ...editForm, email_domains: e.target.value })} placeholder="college.edu, students.college.edu" />
            </div>
            <button className="btn btn-primary" type="submit" disabled={saving}><RefreshCw size={16} /> {saving ? 'Saving…' : 'Save workspace details'}</button>
          </form>
        )}
      </section>

      <section className="card" style={{ marginTop: '1.25rem' }}>
        <div className="card-header"><h2 className="card-title"><Building2 size={18} /> Registered institution workspaces</h2><span className="feature-status">{institutions.length} registered</span></div>
        {loading ? <p>Loading workspaces…</p> : institutions.length === 0 ? <p>No active institution workspaces yet.</p> : (
          <div className="table-responsive">
            <table className="table">
              <thead><tr><th>Institution</th><th>Workspace</th><th>Approved domains</th><th>Status</th><th>Access</th></tr></thead>
              <tbody>{institutions.map((item) => <tr key={item.id}>
                <td>{item.name}</td><td>{item.slug}</td><td>{item.email_domains?.join(', ') || 'Invitation only'}</td><td>{item.status}</td><td><button type="button" className="btn btn-secondary" disabled={saving || item.id === 'INST-DEFAULT'} onClick={() => toggleInstitutionStatus(item)}>{item.status === 'active' ? 'Suspend' : 'Reactivate'}</button></td>
              </tr>)}</tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
