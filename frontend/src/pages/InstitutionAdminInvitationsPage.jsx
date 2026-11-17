import React, { useState } from 'react';
import { ShieldCheck, Users } from 'lucide-react';
import { institutionService } from '../api/services';
import { useAuth } from '../context/AuthContext';

export default function InstitutionAdminInvitationsPage() {
  const { user } = useAuth();
  const [form, setForm] = useState({ name: '', email: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    if (!user?.institution_id) {
      setError('Your account is not linked to an institution. Contact the FixIt platform administrator.');
      return;
    }
    setLoading(true);
    setError('');
    setNotice('');
    try {
      const response = await institutionService.inviteAdmin(user.institution_id, form);
      setNotice(response.data.message || `Invitation sent to ${response.data.email}. It expires in 48 hours.`);
      setForm({ name: '', email: '' });
    } catch (err) {
      setError(err.response?.data?.detail || 'The administrator invitation could not be sent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Invite College Administrator</h1>
          <p className="page-subtitle">Invite another administrator to help manage this institution. They will not receive access to other colleges.</p>
        </div>
      </div>
      <section className="card" style={{ maxWidth: '640px' }}>
        <div className="card-header"><h2 className="card-title"><ShieldCheck size={18} /> Institution administrator invitation</h2></div>
        {error && <div className="form-error" role="alert" style={{ marginBottom: '1rem' }}>{error}</div>}
        {notice && <div role="status" className="card" style={{ marginBottom: '1rem' }}>{notice}</div>}
        <form onSubmit={submit}>
          <div className="form-group">
            <label className="form-label" htmlFor="invite-admin-name">Administrator full name</label>
            <input id="invite-admin-name" className="form-control" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} minLength={2} maxLength={120} required />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="invite-admin-email">Official college email</label>
            <input id="invite-admin-email" type="email" className="form-control" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
          </div>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>The email must use this institution's approved domain. The invitation expires after 48 hours and can be used once. The recipient sets their own password.</p>
          <button type="submit" className="btn btn-primary" disabled={loading || !user?.institution_id}><Users size={16} /> {loading ? 'Sending invitation…' : 'Send invitation'}</button>
        </form>
      </section>
    </div>
  );
}
