import React, { useState, useEffect } from 'react';
import { ShieldAlert, Search, Clock, FileText } from 'lucide-react';
import api from '../api/client';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = actionFilter ? { action: actionFilter } : {};
      const res = await api.get('/audit-logs', { params });
      setLogs(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Immutable Security & Audit Trail</h1>
          <p className="page-subtitle">Non-editable system ledger tracking lifecycle events, authorization overrides, and administrative actions</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <select
            className="form-control"
            style={{ maxWidth: '280px' }}
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            <option value="">All Audit Actions</option>
            <option value="USER_LOGIN">User Logins</option>
            <option value="TICKET_CREATED">Ticket Creations</option>
            <option value="TICKET_STATUS_CHANGED">Status Transitions</option>
            <option value="TICKET_ASSIGNED">Staff Assignments</option>
            <option value="PRIORITY_OVERRIDE">Priority Overrides</option>
            <option value="SLA_POLICY_UPDATED">SLA Policy Updates</option>
          </select>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-subtle)' }}>Loading audit records...</div>
        ) : logs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-subtle)' }}>No audit records recorded yet.</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action Event</th>
                  <th>Resource</th>
                  <th>Actor</th>
                  <th>Details / Changes</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log._id}>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <span style={{
                        fontWeight: '700',
                        fontSize: '0.75rem',
                        fontFamily: 'monospace',
                        color: log.action.includes('OVERRIDE') ? '#DC2626' : log.action.includes('CREATED') ? 'var(--brand-blue)' : 'var(--text-muted)',
                        backgroundColor: 'var(--surface-subtle)',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px'
                      }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8125rem', fontFamily: 'monospace', color: 'var(--brand-blue)' }}>
                      {log.resource_type}:{log.resource_id}
                    </td>
                    <td style={{ fontSize: '0.8125rem' }}>
                      <span style={{ fontWeight: '600', color: 'var(--text-main)' }}>{log.actor?.name}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', display: 'block' }}>({log.actor?.role})</span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: '350px' }}>
                      <code style={{ background: 'var(--bg-main)', padding: '0.25rem', borderRadius: '4px', wordBreak: 'break-all' }}>
                        {JSON.stringify(log.details)}
                      </code>
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
