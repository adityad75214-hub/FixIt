import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PlusCircle, Ticket, Clock, CheckCircle2, AlertTriangle, ArrowRight, BookOpen, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ticketService, knowledgeBaseService } from '../api/services';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import StatCard from '../components/StatCard';
import EmptyState from '../components/EmptyState';

export default function StudentDashboard() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [kbArticles, setKbArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [ticketsRes, kbRes] = await Promise.all([
          ticketService.getTickets({ limit: 50 }),
          knowledgeBaseService.getArticles({ limit: 4 })
        ]);
        setTickets(ticketsRes.data || []);
        setKbArticles(kbRes.data || []);
      } catch (err) {
        console.error("Dashboard load failed:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const total = tickets.length;
  const active = tickets.filter(t => ['open', 'assigned', 'in_progress', 'on_hold', 'reopened'].includes(t.status)).length;
  const resolved = tickets.filter(t => ['resolved', 'closed'].includes(t.status)).length;
  const awaitingFeedback = tickets.filter(t => ['resolved', 'closed'].includes(t.status) && !t.has_feedback).length;

  return (
    <div className="page-wrapper">
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, var(--primary-navy) 0%, var(--primary-navy-dark) 100%)',
        color: '#FFFFFF',
        borderRadius: '12px',
        padding: '1.75rem 2rem',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        boxShadow: 'var(--shadow-md)'
      }}>
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#93C5FD', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {user?.role === 'faculty' ? 'Faculty Portal' : 'Student Portal'}
          </span>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', marginTop: '0.25rem', letterSpacing: '-0.02em' }}>
            Welcome back, {user?.name}
          </h1>
          <p style={{ color: '#BFDBFE', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Department of {user?.department || 'Engineering'} • Campus IT Support
          </p>
        </div>
        <Link to="/tickets/new" className="btn btn-primary" style={{ padding: '0.75rem 1.5rem', fontWeight: '600' }}>
          <PlusCircle size={18} /> Report New Issue
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard label="Recent Tickets" value={total} subtext="Latest 50 tickets" icon={Ticket} color="var(--brand-blue)" bg="var(--brand-blue-light)" />
        <StatCard label="Active / In Progress" value={active} subtext="Under investigation" icon={Clock} color="#F59E0B" bg="#FEF3C7" />
        <StatCard label="Resolved Issues" value={resolved} subtext="Successfully fixed" icon={CheckCircle2} color="#10B981" bg="#D1FAE5" />
        <StatCard label="Action Needed" value={awaitingFeedback} subtext="Confirm or rate service" icon={AlertTriangle} color="#8B5CF6" bg="#EDE9FE" />
      </div>

      {/* Main Grid: Recent Tickets & Knowledge Base */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        {/* Recent Tickets Table */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Ticket size={18} color="var(--brand-blue)" />
              My Recent Complaints
            </h3>
            <Link to="/tickets" style={{ fontSize: '0.8125rem', color: 'var(--brand-blue)', fontWeight: '600' }}>
              View All ({total}) →
            </Link>
          </div>

          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-subtle)' }}>Loading tickets...</div>
          ) : tickets.length === 0 ? (
            <EmptyState
              title="No tickets submitted yet"
              description="Have you experienced any issues with campus Wi-Fi, classroom projectors, or lab computers?"
              action={
                <Link to="/tickets/new" className="btn btn-primary btn-sm">
                  <PlusCircle size={14} /> Report First Issue
                </Link>
              }
            />
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Ticket ID</th>
                    <th>Issue Title</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Location</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontWeight: '600', fontFamily: 'monospace', color: 'var(--brand-blue)', fontSize: '0.8125rem' }}>
                        {t.ticket_id}
                      </td>
                      <td>
                        <div style={{ fontWeight: '600', color: 'var(--text-main)', maxWidth: '220px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {t.title}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {t.category}
                        </div>
                      </td>
                      <td>
                        <PriorityBadge priority={t.priority} />
                      </td>
                      <td>
                        <StatusBadge status={t.status} />
                      </td>
                      <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                        {t.building} - {t.room}
                      </td>
                      <td>
                        <Link to={`/tickets/${t.id}`} className="btn btn-secondary btn-sm">
                          Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Self-Help Guides */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <BookOpen size={18} color="var(--brand-blue)" />
              Self-Help Guides
            </h3>
            <Link to="/knowledge-base" style={{ fontSize: '0.8125rem', color: 'var(--brand-blue)', fontWeight: '600' }}>
              All Guides →
            </Link>
          </div>

          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Instant troubleshooting steps verified by campus IT engineers.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {kbArticles.map((art) => (
              <Link
                key={art.id}
                to={`/knowledge-base?id=${art.id}`}
                style={{
                  padding: '0.75rem',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-main)',
                  border: '1px solid var(--border-color)',
                  transition: 'background 0.15s ease',
                  display: 'block'
                }}
              >
                <div style={{ fontSize: '0.7rem', color: 'var(--brand-blue)', fontWeight: '600', textTransform: 'uppercase' }}>
                  {art.category}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-main)', marginTop: '0.2rem' }}>
                  {art.title}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', marginTop: '0.25rem' }}>
                  👍 {art.helpful_count} upvotes
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
