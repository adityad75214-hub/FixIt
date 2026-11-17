import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Wrench, ArrowRight, ShieldCheck, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { institutionService, authService } from '../api/services';

const initialForm = {
  name: '',
  email: '',
  role: 'student',
  department: '',
  phone: '',
  identifier: '',
  institution_slug: '',
};

export default function RegisterPage() {
  const requestedRole = new URLSearchParams(window.location.search).get('role');
  const startingRole = ['student', 'faculty'].includes(requestedRole) ? requestedRole : 'student';
  const [formData, setFormData] = useState({ ...initialForm, role: startingRole });
  const [institutions, setInstitutions] = useState([]);
  const [step, setStep] = useState('details');
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { completeRegistration } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    institutionService.list().then(({ data }) => {
      setInstitutions(data || []);
      if (data?.length === 1) {
        setFormData((current) => ({ ...current, institution_slug: data[0].slug }));
      }
    }).catch(() => setError('Unable to load colleges. Please refresh and try again.'));
  }, []);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const requestCode = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const { data } = await authService.requestRegistrationCode(formData);
      setStep('verify');
      setMessage(data.message || 'A verification code has been sent to your college email.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to send the verification code.');
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await completeRegistration(formData.email, code, formData.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Email verification failed. Check the code and try again.');
    } finally {
      setLoading(false);
    }
  };

  const selectedInstitution = institutions.find((item) => item.slug === formData.institution_slug);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-main)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '2.5rem 1rem' }}>
      <div style={{ maxWidth: '560px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.75rem' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', backgroundColor: 'var(--primary-navy)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FFFFFF' }}>
              <Wrench size={24} />
            </div>
            <span style={{ fontSize: '1.75rem', fontWeight: '800', color: 'var(--primary-navy)' }}>FixIt</span>
          </Link>
          <h2 style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--text-main)' }}>
            {step === 'details' ? 'Create your campus account' : 'Verify your college email'}
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            {step === 'details' ? 'Register yourself. Your college email verifies your institutional access.' : `Enter the six-digit code sent to ${formData.email}`}
          </p>
        </div>

        <div className="card" style={{ padding: '2rem' }}>
          {error && <div role="alert" style={{ background: '#FEE2E2', border: '1px solid #FCA5A5', color: '#991B1B', padding: '0.75rem 1rem', borderRadius: '6px', fontSize: '0.875rem', marginBottom: '1.25rem' }}>{error}</div>}
          {message && <div role="status" style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', color: '#065F46', padding: '0.75rem 1rem', borderRadius: '6px', fontSize: '0.875rem', marginBottom: '1.25rem' }}>{message}</div>}

          {step === 'details' ? (
            <form onSubmit={requestCode}>
              <div className="form-group">
                <label className="form-label" htmlFor="role">I am registering as</label>
                <select id="role" name="role" className="form-control" value={formData.role} onChange={handleChange}>
                  <option value="student">Student</option>
                  <option value="faculty">Faculty</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="institution_slug">College / Institution</label>
                <select id="institution_slug" name="institution_slug" className="form-control" value={formData.institution_slug} onChange={handleChange} required>
                  <option value="">Select your college</option>
                  {institutions.map((institution) => <option key={institution.id} value={institution.slug}>{institution.name}</option>)}
                </select>
                {selectedInstitution && <small style={{ color: 'var(--text-muted)' }}>Use an email address belonging to {selectedInstitution.name}.</small>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="name">Full name</label>
                <input id="name" name="name" className="form-control" autoComplete="name" value={formData.name} onChange={handleChange} placeholder="Your full name" minLength={2} required />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="email">College email address</label>
                  <input id="email" type="email" name="email" className="form-control" autoComplete="email" value={formData.email} onChange={handleChange} placeholder="you@college.edu" required />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="identifier">{formData.role === 'student' ? 'USN / Student ID' : 'Employee ID'}</label>
                  <input id="identifier" name="identifier" className="form-control" value={formData.identifier} onChange={handleChange} placeholder={formData.role === 'student' ? 'Your USN' : 'Your employee ID'} required />
                </div>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label" htmlFor="department">Department</label>
                  <input id="department" name="department" className="form-control" value={formData.department} onChange={handleChange} placeholder="e.g. Computer Science" required />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="phone">Phone (optional)</label>
                  <input id="phone" type="tel" name="phone" className="form-control" autoComplete="tel" value={formData.phone} onChange={handleChange} placeholder="Phone number" />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', margin: '1rem 0' }}>
                <ShieldCheck size={17} /> First verify your college email. You will create your own password in the next step.
              </div>
              <button type="submit" className="btn btn-navy" style={{ width: '100%', padding: '0.75rem' }} disabled={loading || institutions.length === 0}>
                {loading ? 'Sending verification code…' : 'Send verification code'} <ArrowRight size={16} />
              </button>
            </form>
          ) : (
            <form onSubmit={verifyCode}>
              <div className="form-group">
                <label className="form-label" htmlFor="verification-code">Six-digit verification code</label>
                <input id="verification-code" className="form-control" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="000000" required />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="password">Create your password</label>
                <input id="password" type="password" name="password" className="form-control" autoComplete="new-password" value={formData.password} onChange={handleChange} minLength={12} required />
                <small style={{ color: 'var(--text-muted)' }}>At least 12 characters. This password belongs only to your account.</small>
              </div>
              <button type="submit" className="btn btn-navy" style={{ width: '100%', padding: '0.75rem' }} disabled={loading || code.length !== 6}>
                {loading ? 'Verifying…' : 'Verify email and create account'} <ShieldCheck size={16} />
              </button>
              <button type="button" className="btn btn-secondary" style={{ width: '100%', marginTop: '0.75rem', padding: '0.75rem' }} onClick={() => { setStep('details'); setCode(''); setMessage(''); setError(''); }} disabled={loading}>
                <ArrowLeft size={16} /> Edit registration details
              </button>
            </form>
          )}

          <div style={{ textAlign: 'center', marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--surface-subtle)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--brand-blue)', fontWeight: '600' }}>Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
