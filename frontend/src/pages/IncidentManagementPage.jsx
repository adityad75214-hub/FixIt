import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, ClipboardList, Plus, RefreshCw, ShieldCheck } from 'lucide-react';
import { incidentService, ticketService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import EmptyState from '../components/EmptyState';

const STATUS_LABELS = {
  investigating: 'Investigating',
  identified: 'Cause identified',
  monitoring: 'Monitoring',
  resolved: 'Resolved',
};

const EMPTY_FORM = {
  title: '',
  description: '',
  category: 'Network and Wi-Fi',
  building: '',
  severity: 'high',
  linked_ticket_ids: [],
};

export default function IncidentManagementPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [incidents, setIncidents] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [incidentResponse, ticketResponse] = await Promise.all([
        incidentService.list(),
        ticketService.getTickets(isAdmin ? {} : { assigned_to_me: true }),
      ]);
      setIncidents(incidentResponse.data || []);
      setTickets(ticketResponse.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load incident data.');
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => { load(); }, [load]);

  const toggleTicket = (ticketId) => {
    setForm((current) => ({
      ...current,
      linked_ticket_ids: current.linked_ticket_ids.includes(ticketId)
        ? current.linked_ticket_ids.filter((id) => id !== ticketId)
        : [...current.linked_ticket_ids, ticketId],
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await incidentService.create(form);
      setForm(EMPTY_FORM);
      setFormOpen(false);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create the incident.');
    } finally {
      setSaving(false);
    }
  };

  const updateStatus = async (incident, nextStatus) => {
    try {
      await incidentService.update(incident.id, { status: nextStatus });
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update incident status.');
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Campus Incident Management</h1>
          <p className="page-subtitle">Group related reports into a single campus-wide incident and track investigation progress.</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-secondary" type="button" onClick={load} disabled={loading}><RefreshCw size={16} /> Refresh</button>
          <button className="btn btn-primary" type="button" onClick={() => setFormOpen((open) => !open)}><Plus size={16} /> Create incident</button>
        </div>
      </div>

      {error && <div className="card" role="alert" style={{ marginBottom: '1rem', borderColor: 'var(--danger, #dc2626)' }}>{error}</div>}

      {formOpen && (
        <form className="card incident-form" onSubmit={submit}>
          <h2 className="section-title">Create a master incident</h2>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="incident-title">Incident title</label>
              <input id="incident-title" className="form-control" minLength={5} maxLength={150} required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Wi-Fi outage in Block C" />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="incident-category">Category</label>
              <input id="incident-category" className="form-control" required value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="incident-building">Building (optional)</label>
              <input id="incident-building" className="form-control" value={form.building} onChange={(e) => setForm({ ...form, building: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="incident-severity">Severity</label>
              <select id="incident-severity" className="form-control" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                {['critical', 'high', 'medium', 'low'].map((level) => <option key={level} value={level}>{level[0].toUpperCase() + level.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="incident-description">Description</label>
            <textarea id="incident-description" className="form-control" rows={3} minLength={10} maxLength={3000} required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div className="form-group">
            <span className="form-label">Link related tickets</span>
            <p className="form-help">{isAdmin ? 'Select relevant campus tickets.' : 'Only tickets assigned to you are available to link.'}</p>
            <div className="incident-ticket-picker">
              {tickets.length === 0 ? <p className="text-muted">No eligible tickets available.</p> : tickets.map((ticket) => (
                <label className="incident-ticket-option" key={ticket.id}>
                  <input type="checkbox" checked={form.linked_ticket_ids.includes(ticket.ticket_id)} onChange={() => toggleTicket(ticket.ticket_id)} />
                  <span><strong>{ticket.ticket_id}</strong> — {ticket.title}<small>{ticket.building} · {ticket.status.replaceAll('_', ' ')}</small></span>
                </label>
              ))}
            </div>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setFormOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating…' : 'Create incident'}</button>
          </div>
        </form>
      )}

      {loading ? <div className="card loading-state">Loading incidents…</div> : incidents.length === 0 ? (
        <div className="card"><EmptyState title="No campus incidents yet" description="When several reports describe the same outage or disruption, group them here for coordinated investigation." action={<button className="btn btn-primary btn-sm" onClick={() => setFormOpen(true)}><Plus size={14} /> Create incident</button>} /></div>
      ) : (
        <div className="grid-2">
          {incidents.map((incident) => (
            <article className="card incident-card" key={incident.id}>
              <div className="incident-card-heading">
                <div className="incident-icon"><AlertTriangle size={18} /></div>
                <span className={`feature-status status-${incident.status}`}>{STATUS_LABELS[incident.status] || incident.status}</span>
              </div>
              <div className="incident-id">{incident.id}</div>
              <h2>{incident.title}</h2>
              <p>{incident.description}</p>
              <div className="incident-meta">
                <span>{incident.category}</span>
                <span>{incident.building || 'Campus-wide'}</span>
                <span>{incident.linked_ticket_count} linked tickets</span>
              </div>
              <div className="incident-card-footer">
                <span className={`priority-text priority-${incident.severity}`}>{incident.severity} severity</span>
                {isAdmin ? <select className="form-control" aria-label={`Update status for ${incident.title}`} value={incident.status} onChange={(e) => updateStatus(incident, e.target.value)}>
                  {Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select> : <span className="incident-readonly"><ShieldCheck size={14} /> Tracked</span>}
              </div>
            </article>
          ))}
        </div>
      )}
      <div className="card incident-footnote"><ClipboardList size={18} /><span>Incident records help coordinate related tickets. Individual ticket permissions and technician assignment rules remain in effect.</span></div>
    </div>
  );
}
