import api from './client';

export const authService = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  refresh: () => api.post('/auth/refresh'),
  updateProfile: (data) => api.put('/auth/profile', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  getPreferences: () => api.get('/auth/preferences'),
  updatePreferences: (data) => api.put('/auth/preferences', data),
  uploadFile: (file, purpose, ticketId) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/uploads', form, { params: { purpose, ...(ticketId ? { ticket_id: ticketId } : {}) }, headers: { 'Content-Type': undefined } });
  },
  downloadUpload: (uploadId) => api.get(`/uploads/${uploadId}`, { responseType: 'blob' }),
};

export const ticketService = {
  getTickets: (params) => api.get('/tickets', { params }),
  getTicket: (id) => api.get(`/tickets/${id}`),
  createTicket: (data, autoAssign = true) => api.post(`/tickets?auto_assign=${autoAssign}`, data),
  checkDuplicates: (data) => api.post('/tickets/check-duplicates', data),
  updateStatus: (id, data) => api.put(`/tickets/${id}/status`, data),
  updatePriority: (id, data) => api.put(`/tickets/${id}/priority`, data),
  linkIncident: (id, incidentId) => api.put(`/tickets/${id}/link-incident`, { incident_id: incidentId }),
};

export const assignmentService = {
  getWorkload: () => api.get('/assignments/workload'),
  assignTicket: (ticketId, data) => api.post(`/assignments/${ticketId}/assign`, data),
  autoAssign: (ticketId) => api.post(`/assignments/${ticketId}/auto-assign`),
};

export const commentService = {
  getComments: (ticketId) => api.get(`/comments/ticket/${ticketId}`),
  addComment: (ticketId, data) => api.post(`/comments/ticket/${ticketId}`, data),
};

export const notificationService = {
  getNotifications: () => api.get('/notifications'),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  markAllAsRead: () => api.put('/notifications/mark-all-read'),
};

export const categoryService = {
  getCategories: (includeInactive = false) => api.get(`/categories?include_inactive=${includeInactive}`),
  createCategory: (data) => api.post('/categories', data),
  updateCategory: (id, data) => api.put(`/categories/${id}`, data),
  getLocations: () => api.get('/categories/locations'),
};

export const campusService = {
  getCampuses: () => api.get('/campus'),
  createCampus: (data) => api.post('/campus', data),
  getHierarchy: () => api.get('/campus/hierarchy'),
  getBuildings: () => api.get('/campus/buildings'),
  createBuilding: (data) => api.post('/campus/buildings', data),
  getFloors: (buildingId) => api.get('/campus/floors', { params: { building_id: buildingId } }),
  createFloor: (data) => api.post('/campus/floors', data),
  getRooms: (floorId, buildingId) => api.get('/campus/rooms', { params: { floor_id: floorId, building_id: buildingId } }),
  createRoom: (data) => api.post('/campus/rooms', data),
};

export const slaService = {
  getPolicies: () => api.get('/sla/policies'),
  updatePolicy: (priority, data) => api.put(`/sla/policies/${priority}`, data),
  getOverdueTickets: () => api.get('/sla/overdue-tickets'),
};

export const knowledgeBaseService = {
  getArticles: (params) => api.get('/knowledge-base', { params }),
  getArticle: (id) => api.get(`/knowledge-base/${id}`),
  voteHelpful: (id, helpful) => api.post(`/knowledge-base/${id}/vote`, { helpful }),
  createArticle: (data) => api.post('/knowledge-base', data),
};

export const feedbackService = {
  submitFeedback: (data) => api.post('/feedback', data),
};

export const analyticsService = {
  getDashboardMetrics: () => api.get('/analytics/dashboard'),
};

export const reportService = {
  exportTicketsCSV: (params) => api.get('/reports/export/csv', { params, responseType: 'blob' }),
};

export const auditService = {
  getAuditLogs: (params) => api.get('/audit-logs', { params }),
};

export const userService = {
  getUsers: (params) => api.get('/users', { params }),
  getStaff: () => api.get('/users/staff'),
  createUser: (data) => api.post('/users', data),
  updateUser: (id, data) => api.put(`/users/${id}`, data),
};

export const incidentService = {
  list: () => api.get('/incidents'),
  create: (data) => api.post('/incidents', data),
  update: (id, data) => api.patch(`/incidents/${id}`, data),
};

export const featureRequestService = {
  list: () => api.get('/feature-requests'),
  create: (data) => api.post('/feature-requests', data),
  update: (id, data) => api.patch(`/feature-requests/${id}`, data),
};
