/**
 * Application Controller for Travel Itinerary Generator Platform.
 * Provides offline caching, dark/light mode toggle, and live UI interactivity.
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initOfflineState();
  initNavigationHandlers();
});

function initThemeToggle() {
  const toggleBtn = document.querySelector('.theme-toggle');
  const storedTheme = localStorage.getItem('travel_gen_theme') || 'light';
  document.documentElement.setAttribute('data-theme', storedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const nextTheme = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('travel_gen_theme', nextTheme);
    });
  }
}

function initOfflineState() {
  window.addEventListener('online', () => {
    showToast('Internet restored. Syncing offline changes...');
    flushOfflineSyncQueue();
  });

  window.addEventListener('offline', () => {
    showToast('Offline mode active. Edits are saved locally and will sync automatically.', 'warning');
  });
}

function showToast(message, type = 'info') {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 20px;
      background: var(--surface, #1f2937);
      color: var(--text-primary, #ffffff);
      border: 1px solid var(--border, #374151);
      border-radius: 8px;
      box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0,0,0,0.2));
      z-index: 9999;
      font-size: 0.9rem;
      transition: opacity 0.3s ease;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.opacity = '1';
  setTimeout(() => {
    if (toast) toast.style.opacity = '0';
  }, 4000);
}

function flushOfflineSyncQueue() {
  const queue = JSON.parse(localStorage.getItem('offline_mutations') || '[]');
  if (queue.length === 0) return;

  if (window.TravelAPI && window.TravelAPI.syncDelta) {
    window.TravelAPI.syncDelta(1, {
      client_timestamp: new Date().toISOString(),
      mutations: queue
    }).then(res => {
      showToast(`Successfully synchronized ${res.applied_count || queue.length} offline changes!`);
      localStorage.removeItem('offline_mutations');
    }).catch(err => {
      console.warn('Sync retry queued:', err);
    });
  }
}

function initNavigationHandlers() {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const targetId = link.getAttribute('href').slice(1);
      const target = document.getElementById(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}
