/**
 * Casa Frizzellato — Kiosk & Mobile Dashboard Controller
 * Designed for 24/7 continuous tablet operation with fault tolerance.
 */

(() => {
  'use strict';

  // ---------------------------------------------------------------------------
  // Configuration & Application State
  // ---------------------------------------------------------------------------
  const CONFIG = {
    REFRESH_INTERVAL_MS: 30000, // Regular auto-refresh every 30 seconds
    BASE_RETRY_DELAY_MS: 5000,  // Initial retry delay after failure
    MAX_RETRY_DELAY_MS: 30000,  // Maximum backoff delay
    API_HISTORY_URL: '/api/history',
    API_LATEST_URL: '/api/latest',
  };

  const state = {
    timeframe: localStorage.getItem('cf_timeframe') || '24h',
    visibleSeries: { temp: true, hum: true },
    chart: null,
    isFetching: false,
    refreshTimerId: null,
    retryTimerId: null,
    consecutiveErrors: 0,
    connectionStatus: 'online', // 'online' | 'reconnecting' | 'offline'
    wakeLock: null,
  };

  // ---------------------------------------------------------------------------
  // DOM References
  // ---------------------------------------------------------------------------
  const elements = {
    statusPill: document.getElementById('statusPill'),
    statusText: document.getElementById('statusText'),
    valTemp: document.getElementById('valTemp'),
    valHum: document.getElementById('valHum'),
    cardTemp: document.getElementById('cardTemp'),
    cardHum: document.getElementById('cardHum'),
    legendTemp: document.getElementById('legendTemp'),
    legendHum: document.getElementById('legendHum'),
    lastUpdated: document.getElementById('lastUpdated'),
    timeframeGroup: document.getElementById('timeframeGroup'),
    btnWakeLock: document.getElementById('btnWakeLock'),
    btnFullscreen: document.getElementById('btnFullscreen'),
    toastBanner: document.getElementById('toastBanner'),
    toastMessage: document.getElementById('toastMessage'),
    canvas: document.getElementById('mainChart'),
    tooltip: document.getElementById('chartTooltip'),
  };

  // ---------------------------------------------------------------------------
  // UI & Notification Helpers
  // ---------------------------------------------------------------------------
  function setConnectionStatus(status, message) {
    state.connectionStatus = status;
    elements.statusPill.className = 'status-pill';

    if (status === 'online') {
      elements.statusText.textContent = 'ONLINE';
      hideToast();
    } else if (status === 'reconnecting') {
      elements.statusPill.classList.add('reconnecting');
      elements.statusText.textContent = 'RICONNESSIONE';
      showToast(message || 'Connessione con il sensore interrotta. Riconnessione...', 'warning');
    } else {
      elements.statusPill.classList.add('offline');
      elements.statusText.textContent = 'OFFLINE';
      showToast(message || 'Dispositivo offline. Controlla la rete.', 'danger');
    }
  }

  function showToast(message, type = 'warning') {
    elements.toastMessage.textContent = message;
    elements.toastBanner.className = `toast-banner show ${type}`;
  }

  function hideToast() {
    elements.toastBanner.classList.remove('show');
  }

  function updateTelemetryCards(latestData) {
    if (!latestData) return;

    if (latestData.temperature != null) {
      elements.valTemp.textContent = `${Number(latestData.temperature).toFixed(1)} °C`;
    } else {
      elements.valTemp.textContent = '--.- °C';
    }

    if (latestData.humidity != null) {
      elements.valHum.textContent = `${Number(latestData.humidity).toFixed(1)} %`;
    } else {
      elements.valHum.textContent = '--.- %';
    }

    if (latestData.timestamp) {
      const d = new Date(latestData.timestamp);
      elements.lastUpdated.textContent = `Aggiornato: ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
    }
  }

  // ---------------------------------------------------------------------------
  // Data Fetching with Resilient Error Handling
  // ---------------------------------------------------------------------------
  async function fetchDashboardData() {
    if (state.isFetching) return;
    state.isFetching = true;

    try {
      // Fetch history and latest reading concurrently
      const [historyRes, latestRes] = await Promise.all([
        fetch(`${CONFIG.API_HISTORY_URL}?timeframe=${encodeURIComponent(state.timeframe)}`, {
          headers: { 'Accept': 'application/json' },
          cache: 'no-store',
        }),
        fetch(CONFIG.API_LATEST_URL, {
          headers: { 'Accept': 'application/json' },
          cache: 'no-store',
        }),
      ]);

      if (!historyRes.ok || !latestRes.ok) {
        throw new Error(`HTTP Error: history (${historyRes.status}), latest (${latestRes.status})`);
      }

      const historyData = await historyRes.json();
      const latestData = await latestRes.json();

      // Render chart data and update cards
      if (state.chart) {
        state.chart.setData(historyData.data || []);
      }
      updateTelemetryCards(latestData);

      // Successfully retrieved data -> reset error backoff
      state.consecutiveErrors = 0;
      setConnectionStatus('online');
      scheduleNextRefresh(CONFIG.REFRESH_INTERVAL_MS);

    } catch (err) {
      console.warn('Dashboard fetch error:', err);
      state.consecutiveErrors++;

      // Exponential backoff capped at MAX_RETRY_DELAY_MS
      const delay = Math.min(
        CONFIG.BASE_RETRY_DELAY_MS * Math.pow(1.5, state.consecutiveErrors - 1),
        CONFIG.MAX_RETRY_DELAY_MS
      );

      setConnectionStatus(
        'reconnecting',
        `Connessione persa. Nuovo tentativo tra ${Math.round(delay / 1000)}s...`
      );

      scheduleNextRefresh(delay);
    } finally {
      state.isFetching = false;
    }
  }

  function scheduleNextRefresh(delayMs) {
    if (state.refreshTimerId) {
      clearTimeout(state.refreshTimerId);
    }
    state.refreshTimerId = setTimeout(() => {
      fetchDashboardData();
    }, delayMs);
  }

  // ---------------------------------------------------------------------------
  // Timeframe Filter Buttons
  // ---------------------------------------------------------------------------
  function initTimeframeButtons() {
    elements.timeframeGroup.querySelectorAll('.time-btn').forEach((btn) => {
      const tf = btn.dataset.timeframe;
      if (tf === state.timeframe) {
        btn.classList.add('active');
      }

      btn.addEventListener('click', () => {
        if (state.timeframe === tf) return;

        elements.timeframeGroup.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        state.timeframe = tf;
        localStorage.setItem('cf_timeframe', tf);

        fetchDashboardData();
      });
    });
  }

  // ---------------------------------------------------------------------------
  // Screen Wake Lock API (Tablet Kiosk Keep-Awake)
  // ---------------------------------------------------------------------------
  async function requestWakeLock() {
    if ('wakeLock' in navigator) {
      try {
        state.wakeLock = await navigator.wakeLock.request('screen');
        elements.btnWakeLock.classList.add('active');
        elements.btnWakeLock.title = 'Schermo sempre attivo (ON)';

        state.wakeLock.addEventListener('release', () => {
          elements.btnWakeLock.classList.remove('active');
          elements.btnWakeLock.title = 'Schermo sempre attivo (OFF)';
          state.wakeLock = null;
        });
      } catch (err) {
        console.debug('Wake lock request could not be granted:', err);
      }
    } else {
      elements.btnWakeLock.style.display = 'none';
    }
  }

  async function toggleWakeLock() {
    if (state.wakeLock !== null) {
      await state.wakeLock.release();
      state.wakeLock = null;
    } else {
      await requestWakeLock();
    }
  }

  // ---------------------------------------------------------------------------
  // Fullscreen Management
  // ---------------------------------------------------------------------------
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.debug('Fullscreen request denied:', err);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  function handleFullscreenChange() {
    if (document.fullscreenElement) {
      elements.btnFullscreen.classList.add('active');
      elements.btnFullscreen.title = 'Esci da Schermo Intero';
    } else {
      elements.btnFullscreen.classList.remove('active');
      elements.btnFullscreen.title = 'Schermo Intero';
    }
  }

  // ---------------------------------------------------------------------------
  // Kiosk Lifecycle & Visibility Events
  // ---------------------------------------------------------------------------
  function bindLifecycleEvents() {
    // Re-acquire Wake Lock when tab becomes visible again
    document.addEventListener('visibilitychange', async () => {
      if (document.visibilityState === 'visible') {
        if (state.wakeLock === null) {
          await requestWakeLock();
        }
        // Fetch fresh data immediately upon returning to foreground
        fetchDashboardData();
      }
    });

    // Handle online/offline network transitions
    window.addEventListener('online', () => {
      setConnectionStatus('reconnecting', 'Rete ripristinata. Aggiornamento dati...');
      fetchDashboardData();
    });

    window.addEventListener('offline', () => {
      setConnectionStatus('offline', 'Dispositivo offline. Connessione di rete assente.');
    });

    // Fullscreen listeners
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    elements.btnFullscreen.addEventListener('click', toggleFullscreen);

    // Wake lock toggle button
    elements.btnWakeLock.addEventListener('click', toggleWakeLock);

    // Request wake lock on first user touch / interaction
    const initInteraction = () => {
      requestWakeLock();
      window.removeEventListener('pointerdown', initInteraction);
    };
    window.addEventListener('pointerdown', initInteraction, { once: true });
  }

  // ---------------------------------------------------------------------------
  // Metric Series Filtering (Tap Temp -> Only Temp, Tap Hum -> Only Hum)
  // ---------------------------------------------------------------------------
  function toggleSeriesFilter(targetSeries) {
    const isTempOnly = state.visibleSeries.temp && !state.visibleSeries.hum;
    const isHumOnly = !state.visibleSeries.temp && state.visibleSeries.hum;
    const isBoth = state.visibleSeries.temp && state.visibleSeries.hum;

    if (targetSeries === 'temp') {
      if (isBoth) {
        // Tapped Temp while both visible -> show ONLY Temp
        state.visibleSeries = { temp: true, hum: false };
      } else if (isTempOnly) {
        // Tapped Temp again while already only Temp -> restore both
        state.visibleSeries = { temp: true, hum: true };
      } else {
        // Tapped Temp while only Hum is visible -> switch to ONLY Temp
        state.visibleSeries = { temp: true, hum: false };
      }
    } else if (targetSeries === 'hum') {
      if (isBoth) {
        // Tapped Hum while both visible -> show ONLY Hum
        state.visibleSeries = { temp: false, hum: true };
      } else if (isHumOnly) {
        // Tapped Hum again while already only Hum -> restore both
        state.visibleSeries = { temp: true, hum: true };
      } else {
        // Tapped Hum while only Temp is visible -> switch to ONLY Hum
        state.visibleSeries = { temp: false, hum: true };
      }
    }

    updateFilterUI();
    if (state.chart) {
      state.chart.setVisibleSeries(state.visibleSeries);
    }
  }

  function updateFilterUI() {
    if (elements.cardTemp) {
      elements.cardTemp.classList.toggle('inactive', !state.visibleSeries.temp);
    }
    if (elements.legendTemp) {
      elements.legendTemp.classList.toggle('inactive', !state.visibleSeries.temp);
    }
    if (elements.cardHum) {
      elements.cardHum.classList.toggle('inactive', !state.visibleSeries.hum);
    }
    if (elements.legendHum) {
      elements.legendHum.classList.toggle('inactive', !state.visibleSeries.hum);
    }
  }

  function initSeriesFilterButtons() {
    const bindFilter = (el, type) => {
      if (!el) return;
      el.addEventListener('click', () => toggleSeriesFilter(type));
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleSeriesFilter(type);
        }
      });
    };

    bindFilter(elements.cardTemp, 'temp');
    bindFilter(elements.legendTemp, 'temp');
    bindFilter(elements.cardHum, 'hum');
    bindFilter(elements.legendHum, 'hum');
  }

  // ---------------------------------------------------------------------------
  // Application Entry Point
  // ---------------------------------------------------------------------------
  function init() {
    initTimeframeButtons();
    initSeriesFilterButtons();
    bindLifecycleEvents();

    // Instantiate Canvas Chart Engine
    state.chart = new window.TelemetryChart(elements.canvas, elements.tooltip);

    // Initial fetch
    fetchDashboardData();

    // Attempt wake lock automatically
    requestWakeLock();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
