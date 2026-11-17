import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, Filter, CheckCircle2 } from 'lucide-react';
import { categoryService, ticketService, reportService } from '../api/services';

export default function ReportsPage() {
  const [categories, setCategories] = useState([]);
  const [locations, setLocations] = useState([]);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    category: '',
    building: ''
  });
  const [exporting, setExporting] = useState(false);
  const [ticketCount, setTicketCount] = useState(0);

  useEffect(() => {
    Promise.all([
      categoryService.getCategories(),
      categoryService.getLocations()
    ]).then(([cats, locs]) => {
      setCategories(cats.data || []);
      setLocations(locs.data || []);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    ticketService.getTickets(filters)
      .then(res => setTicketCount(res.data?.length || 0))
      .catch(console.error);
  }, [filters]);

  const handleDownloadCSV = async () => {
    setExporting(true);
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => Boolean(value))
      );
      const response = await reportService.exportTicketsCSV(params);
      const blobUrl = window.URL.createObjectURL(response.data);
      const anchor = document.createElement('a');
      anchor.href = blobUrl;
      anchor.download = `fixit_tickets_export_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error('CSV export failed:', err);
      window.alert(err.response?.data?.detail || 'Could not export the report. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="page-wrapper" style={{ maxWidth: '900px' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports & Data Export</h1>
          <p className="page-subtitle">Generate exportable audit-ready datasets for institutional reporting and quality assurance</p>
        </div>
      </div>

      <div className="card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '1.25rem' }}>
          Select Export Scope & Criteria
        </h3>

        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Status Filter</label>
            <select
              className="form-control"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold">On Hold</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Priority Filter</label>
            <select
              className="form-control"
              value={filters.priority}
              onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
            >
              <option value="">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-control"
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Campus Building</label>
            <select
              className="form-control"
              value={filters.building}
              onChange={(e) => setFilters({ ...filters, building: e.target.value })}
            >
              <option value="">All Buildings</option>
              {locations.map((loc) => (
                <option key={loc.id} value={loc.building}>{loc.building}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Live Filter Summary */}
        <div style={{
          backgroundColor: 'var(--bg-main)',
          borderRadius: '8px',
          padding: '1.25rem',
          border: '1px solid var(--border-color)',
          marginTop: '1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Matching Records Ready to Export:</span>
            <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--primary-navy)' }}>
              {ticketCount} Tickets
            </div>
          </div>

          <button
            className="btn btn-navy"
            style={{ padding: '0.75rem 1.75rem' }}
            disabled={exporting || ticketCount === 0}
            onClick={handleDownloadCSV}
          >
            <Download size={18} /> {exporting ? 'Generating CSV...' : 'Download CSV Report'}
          </button>
        </div>
      </div>
    </div>
  );
}
