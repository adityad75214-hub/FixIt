import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, ShieldAlert, Edit2, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react';
import { slaService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import PriorityBadge from '../components/PriorityBadge';
import Modal from '../components/Modal';

export default function SLAManagementPage() {
  const { user } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [overdueData, setOverdueData] = useState({ overdue_count: 0, tickets: [] });
  const [loading, setLoading] = useState(true);

  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);
  const [formValues, setFormValues] = useState({
    target_resolution_hours: 24,
    target_response_hours: 4,
    description: ''
  });

  const loadSLA = async () => {
    try {
      const [policiesRes, overdueRes] = await Promise.all([
        slaService.getPolicies(),
        slaService.getOverdueTickets()
      ]);
      setPolicies(policiesRes.data || []);
      setOverdueData(overdueRes.data || { overdue_count: 0, tickets: [] });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSLA();
  }, []);

  const handleEditClick = (p) => {
    setEditingPolicy(p);
    setFormValues({
      target_resolution_hours: p.target_resolution_hours,
      target_response_hours: p.target_response_hours,
      description: p.description || ''
    });
    setEditModalOpen(true);
  };

  const handleSavePolicy = async (e) => {
    e.preventDefault();
    try {
      await slaService.updatePolicy(editingPolicy.priority, {
        priority: editingPolicy.priority,
        target_resolution_hours: parseInt(formValues.target_resolution_hours),
        target_response_hours: parseInt(formValues.target_response_hours),
        description: formValues.description
      });
      setEditModalOpen(false);
      loadSLA();
    } catch (err) {
      alert("Failed to update SLA policy");
    }
  };

  const isAdmin = user?.role === 'admin';

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Service Level Agreement (SLA) & Overdue Monitor</h1>
          <p className="page-subtitle">Configure response and resolution target thresholds and monitor compliance</p>
        </div>
      </div>

      {/* SLA Policy Target Cards */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        {policies.map((p) => (
          <div key={p.id} className="card" style={{ borderTop: `4px solid ${p.priority === 'critical' ? '#EF4444' : p.priority === 'high' ? '#F97316' : p.priority === 'medium' ? '#F59E0B' : '#10B981'}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <PriorityBadge priority={p.priority} />
              {isAdmin && (
                <button
                  className="btn btn-secondary btn-sm"
                  style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                  onClick={() => handleEditClick(p)}
                >
                  <Edit2 size={12} /> Edit
                </button>
              )}
            </div>

            <div style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--text-main)', lineHeight: '1.1' }}>
              {p.target_resolution_hours} hrs
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Target Resolution Time
            </div>

            <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--surface-subtle)', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              <span style={{ fontWeight: '600' }}>First Response Target:</span> {p.target_response_hours} hrs
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.35rem', lineHeight: '1.4' }}>
              {p.description}
            </p>
          </div>
        ))}
      </div>

      {/* Live Overdue Queue */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={20} color={overdueData.overdue_count > 0 ? '#EF4444' : '#10B981'} />
            <h3 className="card-title">
              Live Overdue Queue ({overdueData.overdue_count})
            </h3>
          </div>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Active tickets that have exceeded their target SLA resolution window
          </span>
        </div>

        {overdueData.tickets.length === 0 ? (
          <div style={{ padding: '3.5rem', textAlign: 'center' }}>
            <CheckCircle size={36} color="#10B981" style={{ margin: '0 auto 0.75rem auto' }} />
            <h4 style={{ fontWeight: '600', color: '#065F46' }}>Zero SLA Breaches</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>All active support complaints are progressing within their designated resolution windows.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Title & Category</th>
                  <th>Priority</th>
                  <th>Location</th>
                  <th>Assigned Staff</th>
                  <th>Breached By</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {overdueData.tickets.map((t) => (
                  <tr key={t.id} style={{ backgroundColor: '#FEF2F2' }}>
                    <td style={{ fontWeight: '700', fontFamily: 'monospace', color: '#991B1B' }}>
                      {t.ticket_id}
                    </td>
                    <td>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{t.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t.category}</div>
                    </td>
                    <td>
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td style={{ fontSize: '0.8125rem' }}>
                      {t.building} - {t.room}
                    </td>
                    <td style={{ fontSize: '0.8125rem' }}>
                      {t.assigned_to?.name || <span style={{ color: '#DC2626', fontWeight: '600' }}>Unassigned</span>}
                    </td>
                    <td>
                      <span style={{ fontWeight: '700', color: '#DC2626', fontSize: '0.8125rem' }}>
                        +{Math.floor(t.overdue_by_minutes / 60)}h {t.overdue_by_minutes % 60}m late
                      </span>
                    </td>
                    <td>
                      <Link to={`/tickets/${t.id}`} className="btn btn-danger btn-sm">
                        Expedite <ExternalLink size={12} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Policy Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title={`Configure SLA Target: ${editingPolicy?.priority?.toUpperCase()}`}
      >
        <form onSubmit={handleSavePolicy}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Target Resolution Time (Hours) *</label>
              <input
                type="number"
                className="form-control"
                min={1}
                max={240}
                value={formValues.target_resolution_hours}
                onChange={(e) => setFormValues({ ...formValues, target_resolution_hours: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">First Response Target (Hours) *</label>
              <input
                type="number"
                className="form-control"
                min={1}
                max={48}
                value={formValues.target_response_hours}
                onChange={(e) => setFormValues({ ...formValues, target_response_hours: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Policy Description</label>
            <textarea
              className="form-control"
              rows={3}
              value={formValues.description}
              onChange={(e) => setFormValues({ ...formValues, description: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setEditModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-navy">Save Policy</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
