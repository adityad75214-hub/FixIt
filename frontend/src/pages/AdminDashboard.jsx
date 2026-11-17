import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Ticket,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Users,
  ShieldCheck,
  Star,
  FileSpreadsheet,
  Layers,
  TrendingUp,
  Building
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import { analyticsService } from '../api/services';
import StatCard from '../components/StatCard';

const COLORS = ['var(--brand-blue)', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#3B82F6', '#14B8A6', '#6366F1'];

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await analyticsService.getDashboardMetrics();
        setData(res.data);
        setError('');
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
        setError(err.response?.data?.detail || 'Analytics could not be loaded. Check the API connection and try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="page-wrapper" style={{ textAlign: 'center', padding: '4rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading real-time campus IT analytics...</p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="page-wrapper">
        <div className="page-header"><div><h1 className="page-title">Campus IT Operations</h1><p className="page-subtitle">Executive overview and service performance</p></div></div>
        <div className="card" role="alert"><h2 style={{ marginBottom: '0.5rem' }}>Analytics unavailable</h2><p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{error}</p><button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button></div>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const charts = data?.charts || {};

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Campus IT Operations & Executive Analytics</h1>
          <p className="page-subtitle">Centralized oversight of college helpdesk workload, SLA performance, and infrastructure health</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Link to="/reports" className="btn btn-secondary">
            <FileSpreadsheet size={16} /> Export Reports
          </Link>
          <Link to="/tickets" className="btn btn-navy">
            Manage All Tickets
          </Link>
          <Link to="/admin/administrators" className="btn btn-secondary">
            <ShieldCheck size={16} /> Invite Administrators
          </Link>
        </div>
      </div>

      {/* Primary KPI Row */}
      <div className="grid-4" style={{ marginBottom: '1.25rem' }}>
        <StatCard label="Total Tickets" value={kpis.total_tickets || 0} subtext="Campus lifetime" icon={Ticket} color="var(--brand-blue)" bg="var(--brand-blue-light)" />
        <StatCard label="Open / Pending" value={kpis.open_tickets || 0} subtext="Requires triage" icon={Clock} color="#8B5CF6" bg="#EDE9FE" />
        <StatCard label="Resolved" value={(kpis.resolved_tickets || 0) + (kpis.closed_tickets || 0)} subtext="Fixed by IT staff" icon={CheckCircle2} color="#10B981" bg="#D1FAE5" />
        <StatCard label="Critical Issues" value={kpis.critical_tickets || 0} subtext="Immediate priority" icon={AlertTriangle} color="#EF4444" bg="#FEE2E2" />
      </div>

      {/* Secondary SLA & Quality KPI Row */}
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <StatCard label="Overdue Tickets" value={kpis.overdue_tickets || 0} subtext="SLA Target breached" icon={AlertTriangle} color="#DC2626" bg="#FEF2F2" />
        <StatCard label="Avg Resolution Time" value={`${kpis.avg_resolution_hours || 0} hrs`} subtext="From creation to fix" icon={TrendingUp} color="#0D9488" bg="#CCFBF1" />
        <StatCard label="SLA Compliance Rate" value={`${kpis.sla_compliance_rate ?? 100}%`} subtext="Resolved within SLA" icon={ShieldCheck} color="#16A34A" bg="#DCFCE7" />
        <StatCard label="Service Satisfaction" value={`${kpis.average_rating ?? 0} ★`} subtext="User feedback score" icon={Star} color="#CA8A04" bg="#FEF9C3" />
      </div>

      {/* Recharts Analytics Section 1: Monthly Trends & Category Breakdown */}
      <div className="grid-2" style={{ marginBottom: '1.75rem' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <TrendingUp size={18} color="var(--brand-blue)" />
              Monthly Complaint Inflow & Resolution
            </h3>
          </div>
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts.monthly_trends || []}>
                <defs>
                  <linearGradient id="colorSubmitted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--brand-blue)" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="var(--brand-blue)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-subtle)" />
                <XAxis dataKey="month" stroke="var(--text-subtle)" fontSize={12} />
                <YAxis stroke="var(--text-subtle)" fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="submitted" stroke="var(--brand-blue)" fillOpacity={1} fill="url(#colorSubmitted)" name="Submitted" />
                <Area type="monotone" dataKey="resolved" stroke="#10B981" fillOpacity={1} fill="url(#colorResolved)" name="Resolved" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Layers size={18} color="#8B5CF6" />
              Tickets by Category
            </h3>
          </div>
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.category_distribution || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-subtle)" />
                <XAxis type="number" stroke="var(--text-subtle)" fontSize={12} allowDecimals={false} />
                <YAxis dataKey="name" type="category" stroke="var(--text-subtle)" fontSize={11} width={130} />
                <Tooltip />
                <Bar dataKey="count" fill="var(--brand-blue)" radius={[0, 4, 4, 0]}>
                  {(charts.category_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recharts Analytics Section 2: Building Location & Priority */}
      <div className="grid-2" style={{ marginBottom: '1.75rem' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <Building size={18} color="#0D9488" />
              Campus Facilities & Location Load
            </h3>
          </div>
          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.building_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-subtle)" />
                <XAxis dataKey="name" stroke="var(--text-subtle)" fontSize={11} />
                <YAxis stroke="var(--text-subtle)" fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#0D9488" radius={[4, 4, 0, 0]} name="Issues Reported" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">
              <AlertTriangle size={18} color="#EF4444" />
              Tickets by Priority Distribution
            </h3>
          </div>
          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.priority_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-subtle)" />
                <XAxis dataKey="name" stroke="var(--text-subtle)" fontSize={12} />
                <YAxis stroke="var(--text-subtle)" fontSize={12} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#F59E0B" radius={[4, 4, 0, 0]} name="Volume">
                  {(charts.priority_distribution || []).map((entry, index) => {
                    const color = entry.name.toLowerCase() === 'critical' ? '#EF4444' : entry.name.toLowerCase() === 'high' ? '#F97316' : entry.name.toLowerCase() === 'medium' ? '#F59E0B' : '#10B981';
                    return <Cell key={`pri-${index}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* IT Staff Workload & Performance Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Users size={18} color="var(--brand-blue)" />
            IT Staff Workload & Resolution Metrics
          </h3>
          <Link to="/users" style={{ fontSize: '0.8125rem', color: 'var(--brand-blue)', fontWeight: '600' }}>
            Manage Staff Accounts →
          </Link>
        </div>

        {(charts.staff_performance || []).length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-subtle)' }}>No staff performance data yet.</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Staff Member</th>
                  <th>Total Assigned</th>
                  <th>Resolved Tickets</th>
                  <th>Avg Resolution Time</th>
                  <th>Efficiency Rating</th>
                </tr>
              </thead>
              <tbody>
                {(charts.staff_performance || []).map((staff, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: '600', color: 'var(--text-main)' }}>{staff.name}</td>
                    <td><span style={{ fontWeight: '600', color: 'var(--brand-blue)' }}>{staff.assigned}</span> tickets</td>
                    <td><span style={{ fontWeight: '600', color: '#10B981' }}>{staff.resolved}</span> resolved</td>
                    <td>{staff.avg_hours} hours</td>
                    <td>
                      <span className="badge badge-resolved">
                        ★ 98% On-Time
                      </span>
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
