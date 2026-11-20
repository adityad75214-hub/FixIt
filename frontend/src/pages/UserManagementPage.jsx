import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Search, Shield, CheckCircle, XCircle } from 'lucide-react';
import { userService } from '../api/services';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export default function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: '',
    role: 'staff',
    department: 'Network Operations',
    specialization: 'Network and Wi-Fi, Computer and Hardware'
  });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      const res = await userService.getUsers(params);
      setUsers(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [search, roleFilter]);

  const handleToggleActive = async (user) => {
    try {
      await userService.updateUser(user.id, { is_active: !user.is_active });
      fetchUsers();
    } catch (e) {
      alert("Failed to update user status");
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      await userService.createUser({
        ...newUser,
        specialization: newUser.specialization.split(',').map(s => s.trim()).filter(Boolean)
      });
      setCreateModalOpen(false);
      setNewUser({
        name: '',
        email: '',
        password: '',
        role: 'staff',
        department: 'Network Operations',
        specialization: 'Network and Wi-Fi'
      });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to create user account");
    }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">User & Staff Accounts Management</h1>
          <p className="page-subtitle">Provision IT technicians, govern role authorizations, and audit active users</p>
        </div>
        <button className="btn btn-navy" onClick={() => setCreateModalOpen(true)}>
          <UserPlus size={16} /> Create User / Staff Account
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search by name, email, roll or employee ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '2.5rem' }}
            />
            <Search size={18} color="var(--text-subtle)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
          </div>

          <select
            className="form-control"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          >
            <option value="">All Roles</option>
            <option value="student">Student</option>
            <option value="faculty">Faculty</option>
            <option value="staff">IT Staff</option>
            <option value="admin">Administrator</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="card">
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-subtle)' }}>Loading accounts...</div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>User Details</th>
                  <th>Role</th>
                  <th>Department / ID</th>
                  <th>Specialization (Staff)</th>
                  <th>Active Workload</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{u.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{u.email}</div>
                    </td>
                    <td>
                      <span className={`badge badge-${u.role === 'admin' ? 'critical' : u.role === 'staff' ? 'assigned' : u.role === 'faculty' ? 'progress' : 'open'}`}>
                        {u.role.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.8125rem' }}>
                      <div>{u.department || 'Campus'}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>{u.identifier || '-'}</div>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {u.specialization && u.specialization.length > 0 ? u.specialization.join(', ') : '-'}
                    </td>
                    <td>
                      {u.role === 'staff' ? (
                        <span style={{ fontWeight: '600', color: 'var(--brand-blue)', fontSize: '0.8125rem' }}>
                          {u.active_tickets_count || 0} active tickets
                        </span>
                      ) : '-'}
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        fontSize: '0.75rem',
                        fontWeight: '600',
                        color: u.is_active ? '#059669' : '#DC2626'
                      }}>
                        {u.is_active ? <CheckCircle size={14} /> : <XCircle size={14} />}
                        {u.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td>
                      <button
                        className={`btn btn-sm ${u.is_active ? 'btn-secondary' : 'btn-navy'}`}
                        style={{ fontSize: '0.75rem' }}
                        onClick={() => handleToggleActive(u)}
                        disabled={u.id === currentUser?.id && u.is_active}
                        title={u.id === currentUser?.id && u.is_active ? 'You cannot deactivate your own administrator account' : undefined}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create User / Staff Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Provision IT Staff or Campus Account"
      >
        <form onSubmit={handleCreateSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input
              type="text"
              className="form-control"
              value={newUser.name}
              onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
              required
            />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Email *</label>
              <input
                type="email"
                className="form-control"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Password *</label>
              <input
                type="password"
                className="form-control"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                minLength={12}
                required
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Assigned Role</label>
              <select
                className="form-control"
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
              >
                <option value="staff">IT Staff</option>
                <option value="faculty">Faculty</option>
                <option value="student">Student</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Department</label>
              <input
                type="text"
                className="form-control"
                value={newUser.department}
                onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
              />
            </div>
          </div>

          {newUser.role === 'staff' && (
            <div className="form-group">
              <label className="form-label">Technical Specializations (comma separated)</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Network and Wi-Fi, Computer and Hardware, Projector"
                value={newUser.specialization}
                onChange={(e) => setNewUser({ ...newUser, specialization: e.target.value })}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Used by automatic routing to match complaint categories.</span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setCreateModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-navy">Create Account</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
