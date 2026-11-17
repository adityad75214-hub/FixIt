import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BookOpen, Search, ThumbsUp, ThumbsDown, Plus, Eye, Tag, Pencil, Trash2, EyeOff } from 'lucide-react';
import { knowledgeBaseService, categoryService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import Modal from '../components/Modal';

export default function KnowledgeBasePage() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();

  const [articles, setArticles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [search, setSearch] = useState('');
  const [activeArticle, setActiveArticle] = useState(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingArticleId, setEditingArticleId] = useState(null);
  const [articleError, setArticleError] = useState('');
  const [newArticle, setNewArticle] = useState({
    title: '',
    category: '',
    content: '',
    tags: ''
  });

  const fetchArticles = async () => {
    try {
      const params = {};
      if (selectedCategory) params.category = selectedCategory;
      if (search) params.search = search;
      const res = await knowledgeBaseService.getArticles(params);
      setArticles(res.data || []);

      const urlId = searchParams.get('id');
      if (urlId && !activeArticle) {
        const art = res.data?.find(a => a.id === urlId);
        if (art) setActiveArticle(art);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    categoryService.getCategories().then(res => {
      const available = res.data || [];
      setCategories(available);
      setNewArticle(prev => ({
        ...prev,
        category: available.some(item => item.name === prev.category) ? prev.category : (available[0]?.name || '')
      }));
    }).catch(console.error);
  }, []);

  useEffect(() => {
    fetchArticles();
  }, [selectedCategory, search]);

  const handleVote = async (id, helpful) => {
    try {
      await knowledgeBaseService.voteHelpful(id, helpful);
      if (activeArticle && activeArticle.id === id) {
        setActiveArticle(prev => ({
          ...prev,
          helpful_count: helpful ? prev.helpful_count + 1 : prev.helpful_count,
          not_helpful_count: !helpful ? prev.not_helpful_count + 1 : prev.not_helpful_count,
        }));
      }
      fetchArticles();
    } catch (e) {
      window.alert(e.response?.data?.detail || 'Could not record your vote.');
    }
  };

  const openEditArticle = (article) => {
    setEditingArticleId(article.id);
    setNewArticle({ title: article.title, category: article.category, content: article.content, tags: (article.tags || []).join(', '), is_published: article.is_published !== false });
    setArticleError('');
    setCreateModalOpen(true);
  };

  const handleDeleteArticle = async (article) => {
    if (!window.confirm(`Delete “${article.title}”? This also removes its feedback votes.`)) return;
    try {
      await knowledgeBaseService.deleteArticle(article.id);
      if (activeArticle?.id === article.id) setActiveArticle(null);
      await fetchArticles();
    } catch (err) {
      window.alert(err.response?.data?.detail || 'Could not delete article.');
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...newArticle,
        tags: newArticle.tags.split(',').map(t => t.trim()).filter(Boolean)
      };
      if (editingArticleId) {
        await knowledgeBaseService.updateArticle(editingArticleId, payload);
      } else {
        await knowledgeBaseService.createArticle(payload);
      }
      setCreateModalOpen(false);
      setEditingArticleId(null);
      setArticleError('');
      setNewArticle({ title: '', category: categories[0]?.name || '', content: '', tags: '', is_published: true });
      await fetchArticles();
    } catch (err) {
      setArticleError(err.response?.data?.detail || (editingArticleId ? 'Failed to update article.' : 'Failed to create article.'));
    }
  };

  const isStaffOrAdmin = ['staff', 'admin'].includes(user?.role);

  return (
    <div className="page-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Self-Service Knowledge Base & FAQs</h1>
          <p className="page-subtitle">Find verified answers, guides, FAQs, and self-service help across all FixIt support categories</p>
        </div>
        {isStaffOrAdmin && (
          <button className="btn btn-navy" onClick={() => setCreateModalOpen(true)}>
            <Plus size={16} /> New Article
          </button>
        )}
      </div>

      {/* Search Header */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              className="form-control"
              placeholder="Search articles, guides and FAQs..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '2.5rem' }}
            />
            <Search size={18} color="var(--text-subtle)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
          </div>

          <select
            className="form-control"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Articles Grid */}
      {articles.length === 0 && <div className="card" role="status" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No articles found. Try another search or category.</div>}
      <div className="grid-2">
        {articles.map((art) => (
          <div
            key={art.id}
            className="card"
            style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            onClick={() => setActiveArticle(art)}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--brand-blue)', textTransform: 'uppercase' }}>
                  {art.category}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Eye size={12} /> {art.views} views
                </span>
              </div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                {art.title}
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                {art.content.slice(0, 180)}...
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1.25rem', paddingTop: '0.75rem', borderTop: '1px solid var(--surface-subtle)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span>By {art.author_name}</span>
              <span style={{ color: '#059669', fontWeight: '600' }}>
                👍 {art.helpful_count} found helpful
              </span>
              {isStaffOrAdmin && <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.75rem' }} onClick={(e) => e.stopPropagation()}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => openEditArticle(art)}><Pencil size={13} /> Edit</button>
                {art.is_published !== false && <span className="badge badge-assigned">Published</span>}
                {art.is_published === false && <span className="badge">Draft</span>}
                {user?.role === 'admin' && <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleDeleteArticle(art)}><Trash2 size={13} /> Delete</button>}
              </div>}
            </div>
          </div>
        ))}
      </div>

      {/* Read Article Modal */}
      <Modal
        isOpen={!!activeArticle}
        onClose={() => setActiveArticle(null)}
        title={activeArticle?.title || ''}
        maxWidth="700px"
      >
        {activeArticle && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <span className="badge badge-assigned">{activeArticle.category}</span>
              <span>• Published by {activeArticle.author_name}</span>
              <span>• {activeArticle.views} views</span>
            </div>

            <div style={{ fontSize: '0.925rem', color: 'var(--text-muted)', lineHeight: '1.7', whiteSpace: 'pre-line', marginBottom: '1.75rem', maxHeight: '50vh', overflowY: 'auto' }}>
              {activeArticle.content}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: 'var(--bg-main)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--text-main)' }}>Was this article helpful?</span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleVote(activeArticle.id, true)}
                >
                  <ThumbsUp size={14} color="#10B981" /> Yes ({activeArticle.helpful_count})
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleVote(activeArticle.id, false)}
                >
                  <ThumbsDown size={14} color="#EF4444" /> No ({activeArticle.not_helpful_count})
                </button>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Create Article Modal (Staff/Admin) */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => { setCreateModalOpen(false); setEditingArticleId(null); setArticleError(''); }}
        title={editingArticleId ? 'Edit Knowledge Base Article' : 'Create Knowledge Base Article'}
        maxWidth="650px"
      >
        <form onSubmit={handleCreateSubmit}>
          {articleError && <p role="alert" style={{ color: 'var(--danger, #b91c1c)' }}>{articleError}</p>}
          <div className="form-group">
            <label className="form-label">Article Title *</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. How to install VPN on macOS"
              value={newArticle.title}
              onChange={(e) => setNewArticle({ ...newArticle, title: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-control"
              value={newArticle.category}
              onChange={(e) => setNewArticle({ ...newArticle, category: e.target.value })}
            >
              <option value="">Select a category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Content & Troubleshooting Steps *</label>
            <textarea
              className="form-control"
              rows={6}
              placeholder="Enter comprehensive instructions..."
              value={newArticle.content}
              onChange={(e) => setNewArticle({ ...newArticle, content: e.target.value })}
              required
            />
          </div>

          <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}><input type="checkbox" checked={newArticle.is_published !== false} onChange={(e) => setNewArticle({ ...newArticle, is_published: e.target.checked })} /> Publish immediately (uncheck to save as draft)</label>

          <div className="form-group">
            <label className="form-label">Tags (comma-separated)</label>
            <input
              type="text"
              className="form-control"
              placeholder="vpn, macos, network"
              value={newArticle.tags}
              onChange={(e) => setNewArticle({ ...newArticle, tags: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => { setCreateModalOpen(false); setEditingArticleId(null); setArticleError(''); }}>Cancel</button>
            <button type="submit" className="btn btn-navy" disabled={!newArticle.category}>Publish Article</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
