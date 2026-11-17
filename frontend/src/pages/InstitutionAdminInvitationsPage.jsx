import React, { useCallback, useEffect, useState } from 'react';
import { ShieldCheck, Users, UserPlus, Check, X, RefreshCw, UserX, UserCheck } from 'lucide-react';
import { institutionService } from '../api/services';
import { useAuth } from '../context/AuthContext';

export default function InstitutionAdminInvitationsPage() {
  const { user } = useAuth();
  const institutionId = user?.institution_id;
  const isPrimary = user?.admin_level === 'primary';
  const [form, setForm] = useState({ name: '', email: '', designation: '', department: '' });
  const [admins, setAdmins] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    if (!institutionId) return;
    setLoading(true);
    setError('');
    try {
      const [adminResponse, requestResponse] = await Promise.all([
        institutionService.listAdministrators(institutionId),
        isPrimary ? institutionService.listAdministratorRequests(institutionId) : Promise.resolve({ data: [] }),
      ]);
      setAdmins(adminResponse.data || []);
      setRequests(requestResponse.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Administrator information could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, [institutionId, isPrimary]);

  useEffect(() => { load(); }, [load]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true); setError(''); setNotice('');
    try {
      if (isPrimary) {
        const response = await institutionService.inviteAdmin(institutionId, form);
        setNotice(response.data.message || 'Invitation email sent. It expires in 48 hours.');
        setForm({ name: '', email: '', designation: '', department: '' });
      } else {
        const response = await institutionService.requestAdministrator(institutionId, form);
        setNotice(response.data.message || 'Request submitted to the Primary College Admin.');
        setForm({ name: '', email: '', designation: '', department: '' });
      }
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'The administrator action could not be completed.');
    } finally { setSaving(false); }
  };

  const review = async (requestId, approve) => {
    setSaving(true); setError(''); setNotice('');
    try {
      const action = approve ? institutionService.approveAdministratorRequest : institutionService.rejectAdministratorRequest;
      const response = await action(institutionId, requestId);
      setNotice(response.data.message);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'The request could not be reviewed.');
    } finally { setSaving(false); }
  };

  const transferPrimary = async (admin) => {
    if (!window.confirm(`Transfer Primary College Admin ownership to ${admin.name}? You will become a College Admin.`)) return;
    setSaving(true); setError(''); setNotice('');
    try {
      const response = await institutionService.makePrimaryAdministrator(institutionId, admin.id);
      setNotice(response.data.message || 'Primary ownership transferred.');
      window.location.reload();
    } catch (err) {
      setError(err.response?.data?.detail || 'Primary ownership could not be transferred.');
      setSaving(false);
    }
  };

  const toggleAdmin = async (admin) => {
    const next = !admin.is_active;
    if (!window.confirm(`${next ? 'Reactivate' : 'Deactivate'} ${admin.name}?`)) return;
    setSaving(true); setError(''); setNotice('');
    try {
      const response = await institutionService.updateAdministratorStatus(institutionId, admin.id, next);
      setNotice(response.data.message);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Administrator status could not be changed.');
    } finally { setSaving(false); }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Administrator Governance</h1>
          <p className="page-subtitle">Manage administrator access for this college. This workspace cannot view or manage another institution.</p>
        </div>
        <button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw size={16} /> Refresh</button>
      </div>
      {error && <div className="form-error" role="alert" style={{ marginBottom: '1rem' }}>{error}</div>}
      {notice && <div className="card" role="status" style={{ marginBottom: '1rem' }}>{notice}</div>}

      <section className="card" style={{ maxWidth: '760px', marginBottom: '1.5rem' }}>
        <div className="card-header"><h2 className="card-title"><UserPlus size={18} /> {isPrimary ? 'Invite an administrator' : 'Request an administrator'}</h2></div>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {isPrimary
            ? 'As Primary College Admin, you can send invitations directly. The recipient must use an approved college email and set their own password.'
            : 'Your request will be sent to the Primary College Admin. An invitation is sent only after approval.'}
        </p>
        <form onSubmit={submit}>
          <div className="grid-2">
            <div className="form-group"><label className="form-label" htmlFor="admin-name">Full name</label><input id="admin-name" className="form-control" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} minLength={2} maxLength={120} required /></div>
            <div className="form-group"><label className="form-label" htmlFor="admin-email">Official college email</label><input id="admin-email" type="email" className="form-control" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required /></div>
          </div>
          <div className="grid-2">
            <div className="form-group"><label className="form-label" htmlFor="admin-designation">Designation (optional)</label><input id="admin-designation" className="form-control" value={form.designation} onChange={e => setForm({ ...form, designation: e.target.value })} maxLength={120} /></div>
            <div className="form-group"><label className="form-label" htmlFor="admin-department">Department (optional)</label><input id="admin-department" className="form-control" value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} maxLength={100} /></div>
          </div>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>The invitation expires after 48 hours and can be used once. A college administrator cannot grant platform-wide access.</p>
          <button type="submit" className="btn btn-primary" disabled={saving || !institutionId}><ShieldCheck size={16} /> {saving ? 'Processing…' : isPrimary ? 'Send invitation' : 'Submit for approval'}</button>
        </form>
      </section>

      {isPrimary && <section className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header"><h2 className="card-title">Pending administrator requests</h2><span className="badge">{requests.length} pending</span></div>
        {loading ? <p>Loading requests…</p> : requests.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>There are no pending requests.</p> : (
          <div className="table-responsive"><table className="table"><thead><tr><th>Name / Email</th><th>Designation</th><th>Department</th><th>Actions</th></tr></thead><tbody>
            {requests.map(row => <tr key={row.id}><td><strong>{row.name}</strong><br /><small>{row.email}</small></td><td>{row.designation || '—'}</td><td>{row.department || '—'}</td><td style={{ display: 'flex', gap: '.5rem' }}><button className="btn btn-primary" disabled={saving} onClick={() => review(row.id, true)}><Check size={15} /> Approve</button><button className="btn btn-secondary" disabled={saving} onClick={() => review(row.id, false)}><X size={15} /> Reject</button></td></tr>)}
          </tbody></table></div>
        )}
      </section>}

      <section className="card">
        <div className="card-header"><h2 className="card-title"><Users size={18} /> College administrators</h2><span className="badge">{admins.length} total</span></div>
        {loading ? <p>Loading administrators…</p> : admins.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No administrator accounts found.</p> : (
          <div className="table-responsive"><table className="table"><thead><tr><th>Administrator</th><th>Access level</th><th>Status</th>{isPrimary && <th>Action</th>}</tr></thead><tbody>
            {admins.map(admin => <tr key={admin.id}><td><strong>{admin.name}</strong><br /><small>{admin.email}</small></td><td>{admin.admin_level === 'primary' ? 'Primary College Admin' : 'College Admin'}</td><td>{admin.is_active ? 'Active' : 'Inactive'}</td>{isPrimary && <td>{admin.admin_level === 'primary' ? <span style={{ color: 'var(--text-muted)' }}>Owner</span> : <button className="btn btn-secondary" disabled={saving} onClick={() => toggleAdmin(admin)}>{admin.is_active ? <><UserX size={15} /> Deactivate</> : <><UserCheck size={15} /> Reactivate</>}</button>}</td>}</tr>)}
          </tbody></table></div>
        )}
      </section>
    </div>
  );
}
