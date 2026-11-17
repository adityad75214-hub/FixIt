import React, { useCallback, useEffect, useState } from 'react';
import { Lightbulb, Plus, RefreshCw, Send, ClipboardList } from 'lucide-react';
import { featureRequestService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import EmptyState from '../components/EmptyState';

const STATUS_LABELS = {
  submitted: 'Submitted',
  under_review: 'Under review',
  planned: 'Planned',
  in_progress: 'In progress',
  released: 'Released',
  declined: 'Declined',
};

export default function FeatureRequestsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState({ title: '', area: 'General', description: '' });
  const [adminNotes, setAdminNotes] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await featureRequestService.list();
      setItems(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load feature requests.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await featureRequestService.create(form);
      setForm({ title: '', area: 'General', description: '' });
      setFormOpen(false);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit this request.');
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (item, nextStatus) => {
    try {
      await featureRequestService.update(item.id, { status: nextStatus, admin_note: adminNotes[item.id] ?? item.admin_note ?? null });
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update request status.');
    }
  };

  const saveAdminNote = async (item) => {
    try {
      await featureRequestService.update(item.id, { status: item.status, admin_note: adminNotes[item.id] ?? item.admin_note ?? null });
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save the admin note.');
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">{isAdmin ? 'Feature Roadmap' : 'Suggest a Feature'}</h1>
          <p className="page-subtitle">Collect product improvements from campus users and track them through review, planning and release.</p>
        </div>
        <div style={{ display: 'flex', gap: '.6rem', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw size={16} /> Refresh</button>
          <button className="btn btn-primary" onClick={() => setFormOpen(v => !v)}><Plus size={16} /> {isAdmin ? 'Add roadmap item' : 'Suggest feature'}</button>
        </div>
      </div>

      {error && <div className="card" role="alert" style={{ borderColor: '#fca5a5', color: '#b91c1c', marginBottom: '1rem' }}>{error}</div>}

      {formOpen && (
        <form className="card" onSubmit={submit} style={{ marginBottom: '1.25rem' }}>
          <h2 style={{ fontSize: '1rem', marginBottom: '1rem' }}>{isAdmin ? 'Add an item to the roadmap' : 'Submit a feature idea'}</h2>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="feature-title">Feature title</label>
              <input id="feature-title" className="form-control" minLength={5} maxLength={100} required value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="e.g. WhatsApp ticket updates" />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="feature-area">Area</label>
              <select id="feature-area" className="form-control" value={form.area} onChange={e => setForm({ ...form, area: e.target.value })}>
                {['General', 'Ticketing', 'Notifications', 'Knowledge Base', 'Analytics', 'Campus Setup', 'Mobile Experience', 'Administration', 'Security'].map(area => <option key={area}>{area}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="feature-description">What should it do, and why is it useful?</label>
            <textarea id="feature-description" className="form-control" rows={4} minLength={20} maxLength={2000} required value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Describe the problem, who benefits, and the expected behaviour…" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '.6rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setFormOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}><Send size={15} /> {saving ? 'Submitting…' : 'Submit request'}</button>
          </div>
        </form>
      )}

      {loading ? <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Loading roadmap…</div> : items.length === 0 ? (
        <div className="card"><EmptyState title="No feature requests yet" description={isAdmin ? 'Add the first roadmap item or wait for ideas from campus users.' : 'Share an improvement that would make FixIt more useful for your campus.'} action={<button className="btn btn-primary btn-sm" onClick={() => setFormOpen(true)}><Plus size={14} /> Add a suggestion</button>} /></div>
      ) : (
        <div className="grid-2">
          {items.map(item => (
            <article className="card" key={item.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '.75rem', alignItems: 'flex-start' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '.4rem', color: 'var(--brand-blue)', fontSize: '.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.04em' }}><Lightbulb size={14} /> {item.area}</div>
                  <h2 style={{ fontSize: '1.02rem', marginTop: '.45rem', overflowWrap: 'anywhere' }}>{item.title}</h2>
                </div>
                <span className={`feature-status status-${item.status}`}>{STATUS_LABELS[item.status] || item.status}</span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '.875rem', lineHeight: 1.6, margin: '.8rem 0 1rem', whiteSpace: 'pre-wrap' }}>{item.description}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '.5rem', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '.8rem', color: 'var(--text-subtle)', fontSize: '.75rem' }}>
                <span>{isAdmin ? `By ${item.created_by?.name || 'Campus user'} · ${item.created_by?.role || ''}` : `Submitted ${new Date(item.created_at).toLocaleDateString()}`}</span>
                {isAdmin && <select className="form-control" aria-label={`Update status for ${item.title}`} style={{ width: 'auto', minWidth: '145px', padding: '.35rem .5rem' }} value={item.status} onChange={e => updateStatus(item, e.target.value)}>
                  {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>}
              </div>
              {isAdmin && <div style={{ marginTop: '.8rem' }}><label className="form-label" htmlFor={`admin-note-${item.id}`}>Administrator note</label><textarea id={`admin-note-${item.id}`} className="form-control" rows={2} maxLength={1000} value={adminNotes[item.id] ?? item.admin_note ?? ''} onChange={e => setAdminNotes(prev => ({ ...prev, [item.id]: e.target.value }))} placeholder="Add review context or release notes…" /><button className="btn btn-secondary btn-sm" style={{ marginTop: '.45rem' }} onClick={() => saveAdminNote(item)}>Save note</button></div>}
            </article>
          ))}
        </div>
      )}
      <div className="card" style={{ marginTop: '1.25rem', display: 'flex', gap: '.75rem', alignItems: 'flex-start' }}>
        <ClipboardList size={18} color="var(--brand-blue)" />
        <p style={{ fontSize: '.8rem', color: 'var(--text-muted)', lineHeight: 1.55 }}>Roadmap items are tracked here; approving a request does not install code automatically. New functionality still goes through implementation, security review, tests and a deployment.</p>
      </div>
    </div>
  );
}
