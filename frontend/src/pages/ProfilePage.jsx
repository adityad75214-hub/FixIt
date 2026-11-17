import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../api/services';
import { useTheme } from '../context/ThemeContext';

export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const [preferences, setPreferences] = useState({ email_notifications: true, in_app_notifications: true, language: 'en' });
  const [preferencesMsg, setPreferencesMsg] = useState('');
  const [avatarPreview, setAvatarPreview] = useState('');
  const [avatarUploadMsg, setAvatarUploadMsg] = useState('');

  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    department: user?.department || '',
    avatar_url: user?.avatar_url || ''
  });
  const [profileMsg, setProfileMsg] = useState('');

  useEffect(() => {
    let objectUrl;
    const avatar = profileData.avatar_url || '';
    const uploadId = avatar.startsWith('/api/uploads/') ? avatar.slice('/api/uploads/'.length) : '';
    if (/^[a-f0-9]{32}$/.test(uploadId)) {
      authService.downloadUpload(uploadId).then(res => {
        objectUrl = URL.createObjectURL(res.data);
        setAvatarPreview(objectUrl);
      }).catch(() => setAvatarUploadMsg('Could not load saved profile image.'));
    } else {
      setAvatarPreview(avatar);
    }
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [profileData.avatar_url]);

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setAvatarUploadMsg('');
    try {
      const result = await authService.uploadFile(file, 'profile');
      setProfileData(prev => ({ ...prev, avatar_url: result.data.url }));
      setAvatarUploadMsg('Image uploaded. Save your profile to apply it.');
    } catch (err) {
      setAvatarUploadMsg(err.response?.data?.detail || 'Image upload failed.');
    }
  };

  useEffect(() => {
    authService.getPreferences().then(res => setPreferences(res.data)).catch(() => {});
  }, []);

  const handleSavePreferences = async (e) => {
    e.preventDefault();
    try {
      const res = await authService.updatePreferences(preferences);
      setPreferences(res.data);
      setPreferencesMsg('Preferences saved.');
    } catch (err) {
      setPreferencesMsg(err.response?.data?.detail || 'Could not save preferences.');
    }
  };

  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [passMsg, setPassMsg] = useState('');
  const [passError, setPassError] = useState('');

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileMsg('');
    try {
      await authService.updateProfile(profileData);
      setProfileMsg('Profile updated successfully!');
      refreshUser();
    } catch (err) {
      alert("Failed to update profile");
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPassMsg('');
    setPassError('');

    if (passwords.new_password !== passwords.confirm_password) {
      setPassError("New passwords do not match.");
      return;
    }

    try {
      await authService.changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password
      });
      setPassMsg('Password changed. Please sign in again.');
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
      await logout();
      navigate('/login', { replace: true });
    } catch (err) {
      setPassError(err.response?.data?.detail || "Failed to change password");
    }
  };

  return (
    <div className="page-wrapper" style={{ maxWidth: '800px' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">My Profile & Security Settings</h1>
          <p className="page-subtitle">Manage personal contact details and authentication credentials</p>
        </div>
      </div>

      {/* Account Info Summary Card */}
      <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: 'var(--primary-navy)',
          color: '#FFFFFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.75rem',
          fontWeight: '700'
        }}>
          {(avatarPreview || profileData.avatar_url) ? <img src={avatarPreview || profileData.avatar_url} alt="Profile" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} /> : user?.name?.charAt(0).toUpperCase()}
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-main)' }}>{user?.name}</h2>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{user?.email}</div>
          <div style={{ marginTop: '0.25rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span className="badge badge-assigned">{user?.role?.toUpperCase()}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)' }}>Account ID: {user?.id}</span>
          </div>
        </div>
      </div>

      {/* Profile Details Form */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '1rem' }}>
          Personal Information
        </h3>

        {profileMsg && (
          <div style={{ padding: '0.75rem', backgroundColor: '#D1FAE5', color: '#065F46', borderRadius: '6px', fontSize: '0.875rem', marginBottom: '1rem' }}>
            {profileMsg}
          </div>
        )}

        <form onSubmit={handleUpdateProfile}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              type="text"
              className="form-control"
              value={profileData.name}
              onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Profile picture</label>
            <input type="file" className="form-control" accept="image/jpeg,image/png,image/webp,image/gif" onChange={handleAvatarUpload} />
            <small style={{ color: 'var(--text-muted)' }}>Upload JPG, PNG, WEBP or GIF. Maximum size: 5 MB.</small>
            {avatarUploadMsg && <p role="status" style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>{avatarUploadMsg}</p>}
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Academic Department</label>
              <input
                type="text"
                className="form-control"
                value={profileData.department}
                onChange={(e) => setProfileData({ ...profileData, department: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input
                type="text"
                className="form-control"
                placeholder="+1 (555) 000-0000"
                value={profileData.phone}
                onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-navy">Save Profile</button>
          </div>
        </form>
      </div>

      {/* Personal preferences */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '1rem' }}>Preferences</h3>
        {preferencesMsg && <p role="status" style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }}>{preferencesMsg}</p>}
        <form onSubmit={handleSavePreferences}>
          <div className="form-group">
            <label className="form-label">Appearance</label>
            <select className="form-control" value={theme} onChange={(e) => setTheme(e.target.value)}>
              <option value="light">Light theme</option>
              <option value="dark">Dark theme</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Preferred language</label>
            <select className="form-control" value={preferences.language} onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}>
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
            <small style={{ color: 'var(--text-muted)' }}>Saved as your language preference; full interface translation is a separate localization task.</small>
          </div>
          <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <input type="checkbox" checked={preferences.in_app_notifications} onChange={(e) => setPreferences({ ...preferences, in_app_notifications: e.target.checked })} />
            In-app notifications
          </label>
          <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
            <input type="checkbox" checked={preferences.email_notifications} onChange={(e) => setPreferences({ ...preferences, email_notifications: e.target.checked })} />
            Email notification preference
          </label>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-navy">Save Preferences</button>
          </div>
        </form>
      </div>

      {/* Change Password Form */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '1rem' }}>
          Change Password
        </h3>

        {passMsg && (
          <div style={{ padding: '0.75rem', backgroundColor: '#D1FAE5', color: '#065F46', borderRadius: '6px', fontSize: '0.875rem', marginBottom: '1rem' }}>
            {passMsg}
          </div>
        )}

        {passError && (
          <div style={{ padding: '0.75rem', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', fontSize: '0.875rem', marginBottom: '1rem' }}>
            {passError}
          </div>
        )}

        <form onSubmit={handleChangePassword}>
          <div className="form-group">
            <label className="form-label">Current Password</label>
            <input
              type="password"
              className="form-control"
              value={passwords.current_password}
              onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })}
              required
            />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">New Password</label>
              <input
                type="password"
                className="form-control"
                minLength={12}
                value={passwords.new_password}
                onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <input
                type="password"
                className="form-control"
                minLength={12}
                value={passwords.confirm_password}
                onChange={(e) => setPasswords({ ...passwords, confirm_password: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-navy">Update Password</button>
          </div>
        </form>
      </div>
    </div>
  );
}
