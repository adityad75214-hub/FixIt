import React, { useCallback, useEffect, useState } from 'react';
import { Layers3, Plus, Pencil, Power, RefreshCw, Save, X } from 'lucide-react';
import { categoryService } from '../api/services';

const EMPTY_FORM = { name: '', description: '', subcategories: '', icon: 'Wrench', is_active: true };

export default function CategoryManagementPage() {
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const response = await categoryService.getCategories(true);
      setCategories(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load categories.');
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const startEdit = (category) => {
    setEditingId(category.id);
    setForm({ name: category.name, description: category.description || '', subcategories: (category.subcategories || []).join(', '), icon: category.icon || 'Wrench', is_active: category.is_active !== false });
    setFormOpen(true); setSuccess('');
  };

  const reset = () => { setEditingId(null); setForm(EMPTY_FORM); setFormOpen(false); };

  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    const payload = { ...form, name: form.name.trim(), description: form.description.trim() || null, subcategories: form.subcategories.split(',').map(v => v.trim()).filter(Boolean) };
    try {
      if (editingId) await categoryService.updateCategory(editingId, payload);
      else await categoryService.createCategory(payload);
      setSuccess(editingId ? 'Category updated.' : 'Category created.');
      reset(); await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save category.');
    } finally { setSaving(false); }
  };

  const toggleActive = async (category) => {
    setError(''); setSuccess('');
    try {
      await categoryService.updateCategory(category.id, {
        name: category.name,
        description: category.description || null,
        subcategories: category.subcategories || [],
        icon: category.icon || 'Wrench',
        is_active: category.is_active === false,
      });
      setSuccess(`Category ${category.is_active === false ? 'activated' : 'deactivated'}.`);
      await load();
    } catch (err) { setError(err.response?.data?.detail || 'Could not update category status.'); }
  };

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div><h1 className="page-title">Issue Categories</h1><p className="page-subtitle">Manage the issue categories and subcategories available in the ticket form.</p></div>
        <div style={{ display: 'flex', gap: '.6rem' }}><button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw size={16} /> Refresh</button><button className="btn btn-primary" onClick={() => { reset(); setFormOpen(true); }}><Plus size={16} /> Add category</button></div>
      </div>
      {error && <div className="card" role="alert" style={{ borderColor: '#fca5a5', color: '#b91c1c', marginBottom: '1rem' }}>{error}</div>}
      {success && <div className="card" role="status" style={{ borderColor: '#86efac', color: '#047857', marginBottom: '1rem' }}>{success}</div>}
      {formOpen && <form className="card" onSubmit={submit} style={{ marginBottom: '1.25rem' }}>
        <div className="card-header"><h2 className="card-title">{editingId ? 'Edit category' : 'Create category'}</h2><button type="button" className="btn btn-secondary btn-sm" onClick={reset}><X size={14} /> Close</button></div>
        <div className="grid-2">
          <div className="form-group"><label className="form-label" htmlFor="category-name">Category name</label><input id="category-name" className="form-control" required minLength={2} maxLength={80} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
          <div className="form-group"><label className="form-label" htmlFor="category-icon">Icon name</label><input id="category-icon" className="form-control" maxLength={40} value={form.icon} onChange={e => setForm({ ...form, icon: e.target.value })} placeholder="Wrench" /></div>
        </div>
        <div className="form-group"><label className="form-label" htmlFor="category-description">Description</label><input id="category-description" className="form-control" maxLength={300} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></div>
        <div className="form-group"><label className="form-label" htmlFor="category-subs">Subcategories (comma separated)</label><textarea id="category-subs" className="form-control" rows={3} value={form.subcategories} onChange={e => setForm({ ...form, subcategories: e.target.value })} placeholder="Wi-Fi, Router, Network Switch" /></div>
        <label style={{ display: 'flex', gap: '.5rem', alignItems: 'center', marginBottom: '1rem', fontSize: '.85rem' }}><input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} /> Active and available in ticket reporting</label>
        <button className="btn btn-primary" type="submit" disabled={saving}><Save size={15} /> {saving ? 'Saving…' : 'Save category'}</button>
      </form>}
      {loading ? <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading categories…</div> : categories.length === 0 ? <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No categories found.</div> : <div className="grid-2">{categories.map(category => <article className="card" key={category.id}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '.75rem' }}><div style={{ display: 'flex', alignItems: 'center', gap: '.55rem' }}><span className="category-icon"><Layers3 size={17} /></span><div><h2 style={{ fontSize: '1rem' }}>{category.name}</h2><span className={`feature-status ${category.is_active === false ? 'status-declined' : 'status-released'}`}>{category.is_active === false ? 'Inactive' : 'Active'}</span></div></div><div style={{ display: 'flex', gap: '.35rem' }}><button className="btn btn-secondary btn-sm" onClick={() => startEdit(category)} aria-label={`Edit ${category.name}`}><Pencil size={14} /></button><button className="btn btn-secondary btn-sm" onClick={() => toggleActive(category)} aria-label={`${category.is_active === false ? 'Activate' : 'Deactivate'} ${category.name}`}><Power size={14} /></button></div></div>
        {category.description && <p style={{ color: 'var(--text-muted)', fontSize: '.82rem', margin: '.65rem 0' }}>{category.description}</p>}
        <div className="category-tags">{(category.subcategories || []).length ? category.subcategories.map(sub => <span key={sub}>{sub}</span>) : <small>No subcategories configured</small>}</div>
      </article>)}</div>}
    </div>
  );
}
