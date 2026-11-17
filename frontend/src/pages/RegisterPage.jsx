import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Wrench, User, Mail, Lock, Building, Phone, Hash, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'student',
    department: 'Computer Science',
    phone: '',
    identifier: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(formData);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please check your information.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--bg-main)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2.5rem 1rem'
    }}>
      <div style={{ maxWidth: '520px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.75rem' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              backgroundColor: 'var(--primary-navy)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <Wrench size={24} />
            </div>
            <span style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--primary-navy)' }}>FixIt</span>
          </Link>
          <h2 style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--text-main)' }}>Create your campus support account</h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Report technical problems and track resolution progress
          </p>
        </div>

        <div className="card" style={{ padding: '2rem' }}>
          {error && (
            <div style={{
              backgroundColor: '#FEE2E2',
              border: '1px solid #FCA5A5',
              color: '#991B1B',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Account type</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
                <label style={{
                  border: formData.role === 'student' ? '2px solid var(--brand-blue)' : '1px solid var(--border-color)',
                  backgroundColor: formData.role === 'student' ? 'var(--brand-blue-light)' : '#FFFFFF',
                  borderRadius: '8px',
                  padding: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: formData.role === 'student' ? 'var(--brand-blue)' : 'var(--text-muted)'
                }}>
                  <input
                    type="radio"
                    name="role"
                    value="student"
                    checked={formData.role === 'student'}
                    onChange={handleChange}
                    style={{ accentColor: 'var(--brand-blue)' }}
                  />
                  Enrolled Student
                </label>


              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                name="name"
                className="form-control"
                placeholder="e.g. John Doe"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">College Email</label>
                <input
                  type="email"
                  name="email"
                  className="form-control"
                  placeholder="name@college.edu"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  name="password"
                  className="form-control"
                  placeholder="Min 6 characters"
                  value={formData.password}
                  onChange={handleChange}
                  minLength={12}
                  required
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Academic Department</label>
                <select
                  name="department"
                  className="form-control"
                  value={formData.department}
                  onChange={handleChange}
                >
                  <option value="Computer Science">Computer Science</option>
                  <option value="Electrical Engineering">Electrical Engineering</option>
                  <option value="Mechanical Engineering">Mechanical Engineering</option>
                  <option value="Civil Engineering">Civil Engineering</option>
                  <option value="Physics & Mathematics">Physics & Mathematics</option>
                  <option value="Management & Humanities">Management & Humanities</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">{formData.role === 'student' ? 'Roll / Student ID' : 'Faculty ID'}</label>
                <input
                  type="text"
                  name="identifier"
                  className="form-control"
                  placeholder="e.g. 2024-CS-042"
                  value={formData.identifier}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number (Optional)</label>
              <input
                type="text"
                name="phone"
                className="form-control"
                placeholder="+1 (555) 000-0000"
                value={formData.phone}
                onChange={handleChange}
              />
            </div>

            <button
              type="submit"
              className="btn btn-navy"
              style={{ width: '100%', marginTop: '0.75rem', padding: '0.75rem' }}
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Complete Registration'} <ArrowRight size={16} />
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--surface-subtle)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: 'var(--brand-blue)', fontWeight: '600' }}>
              Sign In here
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
