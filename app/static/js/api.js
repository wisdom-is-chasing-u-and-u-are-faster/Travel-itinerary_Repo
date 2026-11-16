/**
 * Client-Side API Integration Layer for Travel Itinerary Generator Platform.
 * Binds frontend views to backend REST endpoints declared in api_contract.json.
 */

const API_BASE = '/api/v1';

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('/api') || endpoint.startsWith('/health') ? endpoint : `${API_BASE}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {})
    }
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: response.statusText, status: response.status };
      }
      throw errorData;
    }
    return await response.json();
  } catch (err) {
    console.error(`API Error on ${url}:`, err);
    throw err;
  }
}

export const TravelAPI = {
  // 1. Health Probe
  checkHealth: () => request('/health'),

  // 2. Itinerary Operations
  generateItinerary: (payload) => request('/itineraries/generate', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  listItineraries: () => request('/itineraries'),
  getItinerary: (id) => request(`/itineraries/${id}`),
  updateItinerary: (id, payload) => request(`/itineraries/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  }),
  addActivity: (id, payload) => request(`/itineraries/${id}/activities`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }),
  updateActivity: (id, activityId, payload) => request(`/itineraries/${id}/activities/${activityId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  }),
  deleteActivity: (id, activityId) => request(`/itineraries/${id}/activities/${activityId}`, {
    method: 'DELETE'
  }),
  syncDelta: (id, payload) => request(`/itineraries/${id}/sync`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }),

  // 3. Workspace Collaborators
  getCollaborators: (tripId) => request(`/workspaces/${tripId}/collaborators`),
  inviteCollaborator: (tripId, payload) => request(`/workspaces/${tripId}/collaborators`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }),

  // 4. Expense Ledger & Settlements
  getExpenses: (tripId) => request(`/expenses/${tripId}`),
  createExpense: (tripId, payload) => request(`/expenses/${tripId}`, {
    method: 'POST',
    body: JSON.stringify(payload)
  }),

  // 5. Affiliates & Recommendations
  getRecommendations: (destination = '') => {
    const q = destination ? `?destination=${encodeURIComponent(destination)}` : '';
    return request(`/affiliates/recommendations${q}`);
  },

  // 6. Tokenized Checkout
  tokenizeCheckout: (payload) => request('/checkout/tokenize', {
    method: 'POST',
    body: JSON.stringify(payload)
  }),

  // 7. Admin Analytics
  getAdminStats: () => request('/admin/stats'),

  // 8. User Profile & Export
  getUserProfile: () => request('/user/profile'),
  updateUserProfile: (payload) => request('/user/profile', {
    method: 'PUT',
    body: JSON.stringify(payload)
  }),
  exportUserData: () => request('/user/export')
};

if (typeof window !== 'undefined') {
  window.TravelAPI = TravelAPI;
}
