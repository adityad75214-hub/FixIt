import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UserCheck, Clock, AlertTriangle, CheckCircle2, ArrowRight, Filter, ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ticketService } from '../api/services';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import StatCard from '../components/StatCard';
import EmptyState from '../components/EmptyState';

export default function StaffDashboard() {
  const { user } = useAuth();
  const [assignedTickets, setAssignedTickets] = useState([]);
  const [openQueue, setOpenQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [assignedRes, openRes] = await Promise.all([
        ticketService.getTickets({ assigned_to_me: true }),
        ticketService.getTickets({ status: 'open' })
      ]);
      setAssignedTickets(assignedRes.data || []);
      setOpenQueue(openRes.data || []);
    } catch (err) {
      console.error("Staff dashboard load failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const myActive = assignedTickets.filter(t => ['assigned', 'in_progress', 'on_hold', 'reopened'].includes(t.status));
  const myResolved = assignedTickets.filter(t => ['resolved', 'closed'].includes(t.status));
  const myOverdue = assignedTickets.filter(t => t.is_overdue && ['assigned', 'in_progress', 'on_hold', 'reopened'].includes(t.status));
  const criticalCount = assignedTickets.filter(t => t.priority === 'critical' && ['assigned', 'in_progress', 'on_hold', 'reopened'].includes(t.status)).length;

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">IT Staff Support Console</h1>
          <p className="page-subtitle">Logged in as {user?.name} • Specializations: {user?.specialization?.join(', ') || 'General IT'}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/sla" className="btn btn-secondary">
            <Clock size={16} /> SLA Monitor
          </Link>
          <Link to="/tickets" className="btn btn-navy">
            View My Queue
          </Link>
        </div>
      </div>

      {/* Overdue Warning Alert */}
      {myOverdue.length > 0 && (
        <div style={{
          backgroundColor: '#FEE2E2',
          border: '1px solid #FCA5A5',
          borderRadius: '10px',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: '#991B1B'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ShieldAlert size={24} />
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.925rem' }}>SLA Breach Alert: {myOverdue.length} Overdue Ticket(s)</div>
              <div style={{ fontSize: '0.8125rem' }}>Please address these tickets immediately to avoid campus escalation.</div>
            </div>
          </div>
          <Link to="/sla" className="btn btn-danger btn-sm">
            Inspect Overdue
          </Link>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard label="My Active Workload" value={myActive.length} subtext="Assigned / In Progress" icon={UserCheck} color="var(--brand-blue)" bg="var(--brand-blue-light)" />
        <StatCard label="Unassigned Campus Queue" value={openQueue.length} subtext="Awaiting pickup" icon={Clock} color="#8B5CF6" bg="#EDE9FE" />
        <StatCard label="Critical Issues" value={criticalCount} subtext="High attention" icon={AlertTriangle} color="#EF4444" bg="#FEE2E2" />
        <StatCard label="My Resolved Total" value={myResolved.length} subtext="Completed successfully" icon={CheckCircle2} color="#10B981" bg="#D1FAE5" />
      </div>

      {/* My Assigned Tickets Table */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">
            <UserCheck size={18} color="var(--brand-blue)" />
            My Assigned Tickets ({assignedTickets.length})
          </h3>
          <Link to="/tickets?assigned_to_me=true" style={{ fontSize: '0.8125rem', color: 'var(--brand-blue)', fontWeight: '600' }}>
            Filtered List →
          </Link>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-subtle)' }}>Loading assignments...</div>
        ) : assignedTickets.length === 0 ? (
          <EmptyState
            title="No tickets assigned to you"
            description="You currently have zero active assignments. Check the open campus queue below to pick up tickets."
          />
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Issue Title & Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Location</th>
                  <th>SLA Remaining</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {assignedTickets.map((t) => (
                  <tr key={t.id} style={{ backgroundColor: t.is_overdue ? '#FEF2F2' : 'inherit' }}>
                    <td style={{ fontWeight: '600', fontFamily: 'monospace', color: 'var(--brand-blue)', fontSize: '0.8125rem' }}>
                      {t.ticket_id}
                    </td>
                    <td>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{t.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t.category} • Reported by {t.created_by?.name}</div>
                    </td>
                    <td>
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td>
                      <StatusBadge status={t.status} />
                    </td>
                    <td style={{ fontSize: '0.8125rem' }}>
                      {t.building} - {t.room}
                    </td>
                    <td>
                      {t.status === 'resolved' || t.status === 'closed' ? (
                        <span style={{ fontSize: '0.75rem', color: '#10B981', fontWeight: '600' }}>Resolved</span>
                      ) : t.is_overdue ? (
                        <span style={{ fontSize: '0.75rem', color: '#EF4444', fontWeight: '700' }}>⚠️ OVERDUE</span>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {Math.floor((t.time_remaining_minutes || 0) / 60)}h {(t.time_remaining_minutes || 0) % 60}m
                        </span>
                      )}
                    </td>
                    <td>
                      <Link to={`/tickets/${t.id}`} className="btn btn-navy btn-sm">
                        Work On Ticket
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Open Unassigned Campus Queue */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Clock size={18} color="#8B5CF6" />
            Unassigned Campus Queue ({openQueue.length})
          </h3>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Open for triage and assignment</span>
        </div>

        {openQueue.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-subtle)', fontSize: '0.875rem' }}>
            No unassigned tickets in the campus queue.
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Location</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {openQueue.map((t) => (
                  <tr key={t.id}>
                    <td style={{ fontWeight: '600', fontFamily: 'monospace', color: 'var(--brand-blue)' }}>{t.ticket_id}</td>
                    <td style={{ fontWeight: '600' }}>{t.title}</td>
                    <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{t.category}</td>
                    <td><PriorityBadge priority={t.priority} /></td>
                    <td style={{ fontSize: '0.8125rem' }}>{t.building} - {t.room}</td>
                    <td>
                      <Link to={`/tickets/${t.id}`} className="btn btn-secondary btn-sm">
                        Accept & Investigate
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
