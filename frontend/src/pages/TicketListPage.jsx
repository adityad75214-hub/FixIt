import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Ticket, Search, Filter, PlusCircle, ArrowUpDown, Clock } from 'lucide-react';
import { ticketService, categoryService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import EmptyState from '../components/EmptyState';

export default function TicketListPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [tickets, setTickets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters state initialized from URL search params
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    status: searchParams.get('status') || '',
    priority: searchParams.get('priority') || '',
    category: searchParams.get('category') || '',
    problem_domain: searchParams.get('problem_domain') || '',
    sort_by: searchParams.get('sort_by') || 'newest',
    assigned_to_me: searchParams.get('assigned_to_me') === 'true'
  });

  useEffect(() => {
    categoryService.getCategories()
      .then(res => setCategories(res.data || []))
      .catch(err => console.error(err));
  }, []);

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.search) params.search = filters.search;
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      if (filters.category) params.category = filters.category;
      if (filters.problem_domain) params.problem_domain = filters.problem_domain;
      if (filters.sort_by) params.sort_by = filters.sort_by;
      if (filters.assigned_to_me) params.assigned_to_me = true;

      const res = await ticketService.getTickets(params);
      setTickets(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [filters]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            {user?.role === 'admin' ? 'Campus IT Tickets Directory' : user?.role === 'staff' ? 'Support Ticket Queue' : 'My Reported Issues'}
          </h1>
          <p className="page-subtitle">Track status, SLA targets, and technician resolution progress</p>
        </div>
        {(user?.role === 'student' || user?.role === 'faculty' || user?.role === 'admin') && (
          <Link to="/tickets/new" className="btn btn-navy">
            <PlusCircle size={16} /> Report New Issue
          </Link>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr repeat(5, minmax(130px, 1fr))', gap: '0.75rem', alignItems: 'center' }}>
          {/* Keyword Search */}
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search by ID, keyword, or room..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              style={{ paddingLeft: '2.25rem' }}
            />
            <Search size={16} color="var(--text-subtle)" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
          </div>

          {/* Status Filter */}
          <select
            className="form-control"
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="on_hold">On Hold</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="reopened">Reopened</option>
          </select>

          {/* Priority Filter */}
          <select
            className="form-control"
            value={filters.priority}
            onChange={(e) => handleFilterChange('priority', e.target.value)}
          >
            <option value="">All Priorities</option>
            <option value="critical">Critical (2h)</option>
            <option value="high">High (8h)</option>
            <option value="medium">Medium (24h)</option>
            <option value="low">Low (72h)</option>
          </select>

          {/* Problem domain filter */}
          <select
            className="form-control"
            aria-label="Filter by problem domain"
            value={filters.problem_domain}
            onChange={(e) => handleFilterChange('problem_domain', e.target.value)}
          >
            <option value="">All problem types</option>
            <option value="technical">Technical</option>
            <option value="academic">Academic</option>
            <option value="administrative">Administrative</option>
            <option value="facilities">Facilities</option>
            <option value="personal_support">Student support</option>
            <option value="community">Community</option>
            <option value="other">Other</option>
          </select>

          {/* Category Filter */}
          <select
            className="form-control"
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.name}>{c.name}</option>
            ))}
          </select>

          {/* Sort By */}
          <select
            className="form-control"
            value={filters.sort_by}
            onChange={(e) => handleFilterChange('sort_by', e.target.value)}
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="priority_high">Highest Priority</option>
            <option value="overdue">Overdue First</option>
          </select>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="card">
        {loading ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-subtle)' }}>Loading tickets...</div>
        ) : tickets.length === 0 ? (
          <EmptyState
            title="No tickets found"
            description="No tickets match the selected filters. Try clearing your search parameters."
          />
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Title & Description</th>
                  <th>Problem Type</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Location</th>
                  <th>Assigned To</th>
                  <th>SLA Remaining</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.id} style={{ backgroundColor: t.is_overdue ? '#FEF2F2' : 'inherit' }}>
                    <td style={{ fontWeight: '700', fontFamily: 'monospace', color: 'var(--brand-blue)', fontSize: '0.8125rem' }}>
                      {t.ticket_id}
                    </td>
                    <td>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {t.title}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Reported by {t.created_by?.name} ({t.created_by?.role})
                      </div>
                    </td>
                    <td style={{ fontSize: '0.8125rem', textTransform: 'capitalize' }}>{(t.problem_domain || 'technical').replaceAll('_', ' ')}</td>
                    <td style={{ fontSize: '0.8125rem' }}>{t.category}</td>
                    <td>
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td>
                      <StatusBadge status={t.status} />
                    </td>
                    <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                      {t.building} - {t.room}
                    </td>
                    <td style={{ fontSize: '0.8125rem' }}>
                      {t.assigned_to ? (
                        <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{t.assigned_to.name}</span>
                      ) : (
                        <span style={{ color: 'var(--text-subtle)', fontStyle: 'italic' }}>Unassigned</span>
                      )}
                    </td>
                    <td>
                      {t.status === 'resolved' || t.status === 'closed' ? (
                        <span style={{ fontSize: '0.75rem', color: '#10B981', fontWeight: '600' }}>Resolved</span>
                      ) : t.is_overdue ? (
                        <span style={{ fontSize: '0.75rem', color: '#EF4444', fontWeight: '700' }}>⚠️ Overdue</span>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {Math.floor((t.time_remaining_minutes || 0) / 60)}h {(t.time_remaining_minutes || 0) % 60}m
                        </span>
                      )}
                    </td>
                    <td>
                      <Link to={`/tickets/${t.id}`} className="btn btn-secondary btn-sm">
                        View
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
