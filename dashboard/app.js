// Frontend logic: fetch data and render two ApexCharts (temperature + humidity)

const API_BASE = '/api'; // assumes backend served from same host:port

const state = {
  timeframe: '24h',
  chartTemp: null,
  chartHum: null,
  isUpdating: false,
  refreshTimerId: null,
  refreshIntervalMs: 60 * 1000, // 60 seconds
};

function isoToLocal(ts) {
  const d = new Date(ts);
  return d.toLocaleString();
}

async function fetchData(timeframe) {
  const res = await fetch(`${API_BASE}/data?timeframe=${timeframe}`);
  if (!res.ok) throw new Error('Failed to fetch data');
  const data = await res.json();
  return data;
}

function mapSeries(data) {
  // data: [{timestamp, temperature, humidity}, ...]
  const labels = data.map(d => d.timestamp);
  const rawTemps = data.map(d => d.temperature === null ? null : Number(Number(d.temperature).toFixed(2)));
  const rawHums = data.map(d => d.humidity === null ? null : Number(Number(d.humidity).toFixed(2)));

  // Forward-fill nulls so short gaps don't break the line (helps dense 24h slots)
  function forwardFill(arr) {
    const out = [];
    let last = null;
    for (let i = 0; i < arr.length; i++) {
      const v = arr[i];
      if (v === null || v === undefined) {
        out.push(last);
      } else {
        out.push(v);
        last = v;
      }
    }
    return out;
  }

  const temps = forwardFill(rawTemps);
  const hums = forwardFill(rawHums);
  return { labels, temps, hums };
}

function createCharts(labels, temps, hums) {
  const commonOptions = {
    chart: { toolbar: { show: false }, animations: { enabled: true, easing: 'easeout', speed: 600 } },
    stroke: { width: 2, curve: 'smooth' },
    xaxis: { type: 'datetime', categories: labels, labels: { style: { colors: '#94a3b8' } } },
    tooltip: {
      theme: 'dark',
      x: {
        // show full local date + time in tooltip
        formatter: function (val) {
          try {
            return new Date(val).toLocaleString();
          } catch (e) {
            return val;
          }
        }
      }
    },
    theme: { mode: 'dark', palette: 'palette4' },
  };

  const tempOptions = Object.assign({}, commonOptions, {
    series: [{ name: 'Temperatura (°C)', data: temps }],
    yaxis: { title: { text: '°C' }, labels: { style: { colors: '#fb7185' } } },
    colors: ['#fb7185'],
  });

  const humOptions = Object.assign({}, commonOptions, {
    series: [{ name: 'Umidità (%)', data: hums }],
    yaxis: { title: { text: '%' }, labels: { style: { colors: '#60a5fa' } } },
    colors: ['#60a5fa'],
  });

  if (state.chartTemp) state.chartTemp.destroy();
  if (state.chartHum) state.chartHum.destroy();

  state.chartTemp = new ApexCharts(document.querySelector('#chart-temp'), tempOptions);
  state.chartHum = new ApexCharts(document.querySelector('#chart-hum'), humOptions);

  state.chartTemp.render();
  state.chartHum.render();
}

async function updateCharts(timeframe, firstLoad = false) {
  if (state.isUpdating) return; // avoid overlapping refreshes
  state.isUpdating = true;
  const container = document.querySelector('#chart-temp').closest('div');
  try {
    container.classList.add('opacity-60');
    const raw = await fetchData(timeframe);
    const { labels, temps, hums } = mapSeries(raw);
    if (firstLoad) {
      createCharts(labels, temps, hums);
    } else {
      // Smooth update via updateOptions / updateSeries
      state.chartTemp.updateOptions({ xaxis: { categories: labels } });
      state.chartHum.updateOptions({ xaxis: { categories: labels } });
      state.chartTemp.updateSeries([{ name: 'Temperatura (°C)', data: temps }], true);
      state.chartHum.updateSeries([{ name: 'Umidità (%)', data: hums }], true);
    }
  } catch (err) {
    console.error(err);
    // show basic inline message
    container.insertAdjacentHTML('beforeend', '<div class="text-red-400 mt-2">Error loading data</div>');
  } finally {
    container.classList.remove('opacity-60');
    state.isUpdating = false;
  }
}

function setActiveButton(btnId) {
  document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('ring-2', 'ring-offset-2', 'ring-indigo-500'));
  const el = document.getElementById(btnId);
  if (el) el.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-500');
}

function bindButtons() {
  document.getElementById('btn-24h').addEventListener('click', async () => {
    state.timeframe = '24h';
    setActiveButton('btn-24h');
    await updateCharts('24h');
  });
  document.getElementById('btn-7d').addEventListener('click', async () => {
    state.timeframe = '7d';
    setActiveButton('btn-7d');
    await updateCharts('7d');
  });
  document.getElementById('btn-1m').addEventListener('click', async () => {
    state.timeframe = '1m';
    setActiveButton('btn-1m');
    await updateCharts('1m');
  });
}

// Initialize
function startAutoRefresh(){
  if (state.refreshTimerId) return;
  state.refreshTimerId = setInterval(()=>{
    // don't force firstLoad so charts update smoothly
    updateCharts(state.timeframe, false).catch(e=>console.error('Auto-refresh failed', e));
  }, state.refreshIntervalMs);
}

function stopAutoRefresh(){
  if (!state.refreshTimerId) return;
  clearInterval(state.refreshTimerId);
  state.refreshTimerId = null;
}

async function init() {
  bindButtons();
  setActiveButton('btn-24h');
  try {
    await updateCharts(state.timeframe, true);
  } catch (e) {
    console.error('Initial update failed', e);
  }
  startAutoRefresh();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  // DOM already ready (script may have been loaded dynamically) — run immediately
  init();
}

window.addEventListener('beforeunload', ()=>{
  stopAutoRefresh();
});
