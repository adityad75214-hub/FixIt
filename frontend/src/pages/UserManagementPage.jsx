import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Search, Shield, CheckCircle, XCircle } from 'lucide-react';
import { userService, categoryService } from '../api/services';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export default function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [issueCategories, setIssueCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(false);

  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: '',
    role: 'staff',
    department: '',
    specialization: []
  });

  const fetchIssueCategories = async () => {
    setCategoriesLoading(true);
    try {
      const res = await categoryService.getCategories(false);
      setIssueCategories((res.data || []).filter(category => category.is_active !== false));
    } catch (error) {
      console.error('Failed to load issue categories', error);
      setIssueCategories([]);
    } finally {
      setCategoriesLoading(false);
    }
  };

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

  useEffect(() => {
    fetchIssueCategories();
  }, []);

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
    if (newUser.role === 'staff' && newUser.specialization.length === 0) {
      alert('Select at least one issue category for this staff member.');
      return;
    }
    try {
      await userService.createUser(newUser);
      setCreateModalOpen(false);
      setNewUser({
        name: '',
        email: '',
        password: '',
        role: 'staff',
        department: '',
        specialization: []
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
          <p className="page-subtitle">Manage college users and assign staff to the issue categories they handle</p>
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
            <option value="staff">Staff</option>
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
                  <th>Issue Categories (Staff)</th>
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
        title="Create User or Staff Account"
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
                <option value="staff">Staff</option>
                <option value="admin">Administrator</option>
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
              <label className="form-label">Issue Categories handled *</label>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '-0.35rem' }}>
                Select every active Issue Category this staff member can handle. These categories are loaded from Issue Categories and used for ticket routing.
              </p>
              {categoriesLoading ? (
                <div className="form-control" style={{ color: 'var(--text-muted)' }}>Loading issue categories…</div>
              ) : issueCategories.length === 0 ? (
                <div className="form-control" style={{ color: 'var(--text-muted)' }}>
                  No active issue categories found. Add or activate categories in Issue Categories first.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '.5rem', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '.85rem', maxHeight: '220px', overflowY: 'auto' }}>
                  {issueCategories.map(category => (
                    <label key={category.id} style={{ display: 'flex', alignItems: 'center', gap: '.55rem', fontSize: '.85rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={newUser.specialization.includes(category.name)}
                        onChange={(event) => setNewUser({
                          ...newUser,
                          specialization: event.target.checked
                            ? [...newUser.specialization, category.name]
                            : newUser.specialization.filter(name => name !== category.name)
                        })}
                      />
                      <span>{category.name}</span>
                    </label>
                  ))}
                </div>
              )}
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Selected: {newUser.specialization.length}. A staff member can handle multiple categories.
              </span>
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
