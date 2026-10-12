/**
 * High-performance, zero-dependency dual-axis Canvas 2D charting engine.
 * Designed for 24/7 continuous kiosk operation:
 * - Zero memory leaks (reuses arrays, no DOM creation on render loops)
 * - Automatic High-DPI (Retina) device pixel ratio scaling
 * - Dual Y-Axis: Left for Temperature (°C), Right for Humidity (% RH)
 * - Touch & pointer interaction with crosshair and synchronized tooltip
 * - Catmull-Rom smooth spline rendering with gradient fills
 */

class TelemetryChart {
  constructor(canvasElement, tooltipElement) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d', { alpha: true });
    this.tooltip = tooltipElement;

    this.data = []; // [{ timestamp: Date, temperature: number|null, humidity: number|null }]
    this.visibleSeries = { temp: true, hum: true };
    this.activePointIndex = null;
    this.animFrameId = null;

    // Margins around the plotting area (pixels)
    this.margins = {
      top: 28,
      right: 68,  // Space for right axis labels (Humidity)
      bottom: 40, // Space for bottom axis labels (Time)
      left: 68,   // Space for left axis labels (Temperature)
    };

    // Styling constants
    this.colors = {
      temp: '#ff6b6b',
      tempFillStart: 'rgba(255, 107, 107, 0.22)',
      tempFillEnd: 'rgba(255, 107, 107, 0.00)',
      hum: '#22d3ee',
      humFillStart: 'rgba(34, 211, 238, 0.16)',
      humFillEnd: 'rgba(34, 211, 238, 0.00)',
      grid: 'rgba(255, 255, 255, 0.06)',
      crosshair: 'rgba(255, 255, 255, 0.35)',
      axisText: '#94a3b8',
      font: '600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontBold: 'bold 15px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      timeFont: '600 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    };

    this._setupCanvas();
    this._bindEvents();
  }

  _setupCanvas() {
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(this.canvas.parentElement);
    this.resize();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    this.width = Math.max(rect.width, 100);
    this.height = Math.max(rect.height, 100);

    this.canvas.width = Math.floor(this.width * dpr);
    this.canvas.height = Math.floor(this.height * dpr);
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;

    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.render();
  }

  setData(points) {
    if (!Array.isArray(points)) {
      this.data = [];
    } else {
      this.data = points.map(p => ({
        timestamp: p.timestamp instanceof Date ? p.timestamp : new Date(p.timestamp),
        temperature: p.temperature != null ? Number(p.temperature) : null,
        humidity: p.humidity != null ? Number(p.humidity) : null,
      })).filter(p => !isNaN(p.timestamp.getTime()));
    }

    if (this.activePointIndex !== null && this.activePointIndex >= this.data.length) {
      this.activePointIndex = null;
      this._hideTooltip();
    }

    this.render();
  }

  setVisibleSeries(visibility) {
    if (!visibility) return;
    this.visibleSeries = {
      temp: visibility.temp !== undefined ? Boolean(visibility.temp) : true,
      hum: visibility.hum !== undefined ? Boolean(visibility.hum) : true,
    };
    this.render();
  }

  _bindEvents() {
    const handlePointer = (evt) => {
      if (!this.data.length) return;
      const rect = this.canvas.getBoundingClientRect();
      const x = evt.clientX - rect.left;
      const y = evt.clientY - rect.top;

      const plotLeft = this.margins.left;
      const plotRight = this.width - this.margins.right;

      if (x < plotLeft - 10 || x > plotRight + 10) {
        this.activePointIndex = null;
        this._hideTooltip();
        this.render();
        return;
      }

      const clampedX = Math.max(plotLeft, Math.min(plotRight, x));
      const ratio = (clampedX - plotLeft) / (plotRight - plotLeft);
      const targetTime = this.minTime + ratio * (this.maxTime - this.minTime);

      // Find closest point by binary search or direct scan
      let closestIdx = 0;
      let minDiff = Infinity;
      for (let i = 0; i < this.data.length; i++) {
        const diff = Math.abs(this.data[i].timestamp.getTime() - targetTime);
        if (diff < minDiff) {
          minDiff = diff;
          closestIdx = i;
        }
      }

      this.activePointIndex = closestIdx;
      this._showTooltip(closestIdx, clampedX, y);
      this.render();
    };

    this.canvas.addEventListener('pointerdown', handlePointer, { passive: true });
    this.canvas.addEventListener('pointermove', handlePointer, { passive: true });
    this.canvas.addEventListener('pointerleave', () => {
      this.activePointIndex = null;
      this._hideTooltip();
      this.render();
    });
    this.canvas.addEventListener('pointerup', () => {
      // Keep crosshair visible for a moment on touch screens
    });
  }

  _showTooltip(index, px, py) {
    if (!this.tooltip || index < 0 || index >= this.data.length) return;
    const pt = this.data[index];

    const timeStr = pt.timestamp.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    let rowsHtml = '';
    if (this.visibleSeries.temp) {
      const tempStr = pt.temperature != null ? `${pt.temperature.toFixed(1)} °C` : '--';
      rowsHtml += `<div class="tooltip-row temp"><span>Temperatura</span><span>${tempStr}</span></div>`;
    }
    if (this.visibleSeries.hum) {
      const humStr = pt.humidity != null ? `${pt.humidity.toFixed(1)} %` : '--';
      rowsHtml += `<div class="tooltip-row hum"><span>Umidità</span><span>${humStr}</span></div>`;
    }

    if (!rowsHtml) {
      this._hideTooltip();
      return;
    }

    this.tooltip.innerHTML = `
      <div class="tooltip-time">${timeStr}</div>
      ${rowsHtml}
    `;

    this.tooltip.style.display = 'block';

    // Constrain tooltip horizontally within canvas box
    const tooltipRect = this.tooltip.getBoundingClientRect();
    const halfWidth = tooltipRect.width / 2;
    const clampedX = Math.max(halfWidth + 8, Math.min(this.width - halfWidth - 8, px));

    this.tooltip.style.left = `${clampedX}px`;
    this.tooltip.style.top = `${Math.max(this.margins.top + 30, py)}px`;
  }

  _hideTooltip() {
    if (this.tooltip) {
      this.tooltip.style.display = 'none';
    }
  }

  _computeExtents() {
    if (!this.data.length) {
      const now = Date.now();
      return {
        minTime: now - 86400000,
        maxTime: now,
        minTemp: 15,
        maxTemp: 30,
        minHum: 30,
        maxHum: 80,
      };
    }

    let minTime = this.data[0].timestamp.getTime();
    let maxTime = this.data[this.data.length - 1].timestamp.getTime();
    if (maxTime <= minTime) maxTime = minTime + 3600000;

    let minTemp = Infinity, maxTemp = -Infinity;
    let minHum = Infinity, maxHum = -Infinity;

    for (let i = 0; i < this.data.length; i++) {
      const t = this.data[i].temperature;
      const h = this.data[i].humidity;
      if (t != null) {
        if (t < minTemp) minTemp = t;
        if (t > maxTemp) maxTemp = t;
      }
      if (h != null) {
        if (h < minHum) minHum = h;
        if (h > maxHum) maxHum = h;
      }
    }

    // Default fallbacks if all points were null
    if (minTemp === Infinity) { minTemp = 15; maxTemp = 30; }
    if (minHum === Infinity) { minHum = 30; maxHum = 80; }

    // Add 10% breathing room to temperature scale
    const tempSpan = Math.max(maxTemp - minTemp, 2.0);
    minTemp = Math.floor(minTemp - tempSpan * 0.08);
    maxTemp = Math.ceil(maxTemp + tempSpan * 0.08);

    // Add breathing room to humidity scale (bounded within 0 - 100)
    const humSpan = Math.max(maxHum - minHum, 5.0);
    minHum = Math.max(0, Math.floor((minHum - humSpan * 0.08) / 5) * 5);
    maxHum = Math.min(100, Math.ceil((maxHum + humSpan * 0.08) / 5) * 5);

    return { minTime, maxTime, minTemp, maxTemp, minHum, maxHum };
  }

  render() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    this.animFrameId = requestAnimationFrame(() => this._paint());
  }

  _paint() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    ctx.clearRect(0, 0, w, h);

    if (!w || !h) return;

    const extents = this._computeExtents();
    this.minTime = extents.minTime;
    this.maxTime = extents.maxTime;
    const { minTemp, maxTemp, minHum, maxHum } = extents;

    const showTemp = this.visibleSeries.temp;
    const showHum = this.visibleSeries.hum;

    const pLeft = showTemp ? this.margins.left : 24;
    const pRight = w - (showHum ? this.margins.right : 24);
    const pTop = this.margins.top;
    const pBottom = h - this.margins.bottom;
    const pWidth = pRight - pLeft;
    const pHeight = pBottom - pTop;

    if (pWidth <= 0 || pHeight <= 0) return;

    // Helper conversion functions
    const xForTime = (timeMs) => pLeft + ((timeMs - this.minTime) / (this.maxTime - this.minTime)) * pWidth;
    const yForTemp = (temp) => pBottom - ((temp - minTemp) / (maxTemp - minTemp)) * pHeight;
    const yForHum = (hum) => pBottom - ((hum - minHum) / (maxHum - minHum)) * pHeight;

    // 1. Draw Horizontal Gridlines & Y-Axis Labels
    const numYSteps = 5;
    ctx.textBaseline = 'middle';
    ctx.font = this.colors.font;

    for (let i = 0; i <= numYSteps; i++) {
      const stepRatio = i / numYSteps;
      const y = pBottom - stepRatio * pHeight;

      // Grid line
      ctx.strokeStyle = this.colors.grid;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pLeft, y);
      ctx.lineTo(pRight, y);
      ctx.stroke();

      // Left axis label (Temperature °C)
      if (showTemp) {
        const tVal = minTemp + stepRatio * (maxTemp - minTemp);
        ctx.textAlign = 'right';
        ctx.fillStyle = this.colors.temp;
        ctx.fillText(`${tVal.toFixed(1)}°`, pLeft - 10, y);
      }

      // Right axis label (Humidity %)
      if (showHum) {
        const hVal = Math.round(minHum + stepRatio * (maxHum - minHum));
        ctx.textAlign = 'left';
        ctx.fillStyle = this.colors.hum;
        ctx.fillText(`${hVal}%`, pRight + 10, y);
      }
    }

    // Axis Unit Header Labels
    ctx.font = this.colors.fontBold;
    if (showTemp) {
      ctx.fillStyle = this.colors.temp;
      ctx.textAlign = 'right';
      ctx.fillText('°C', pLeft - 10, pTop - 12);
    }

    if (showHum) {
      ctx.fillStyle = this.colors.hum;
      ctx.textAlign = 'left';
      ctx.fillText('%', pRight + 10, pTop - 12);
    }

    // 2. Draw Time X-Axis Ticks & Labels
    const numXSteps = w > 600 ? 6 : 4;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = this.colors.axisText;
    ctx.font = this.colors.timeFont;

    const timeSpan = this.maxTime - this.minTime;
    const isMultiDay = timeSpan > 36 * 3600000;

    for (let i = 0; i <= numXSteps; i++) {
      const tMs = this.minTime + (i / numXSteps) * timeSpan;
      const x = pLeft + (i / numXSteps) * pWidth;
      const d = new Date(tMs);

      let label = '';
      if (isMultiDay) {
        label = d.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      } else {
        label = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
      }

      ctx.fillText(label, x, pBottom + 12);
    }

    if (!this.data.length || (!showTemp && !showHum)) {
      ctx.fillStyle = this.colors.axisText;
      ctx.font = '15px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const msg = !this.data.length
        ? 'Nessun dato registrato per il periodo selezionato'
        : 'Tutti i grafici sono nascosti. Tocca Temperatura o Umidità per visualizzare.';
      ctx.fillText(msg, w / 2, h / 2);
      return;
    }

    // 3. Draw Humidity Series (Area + Spline)
    if (showHum) {
      this._drawSeries({
        ctx,
        points: this.data,
        xFn: (p) => xForTime(p.timestamp.getTime()),
        yFn: (p) => p.humidity != null ? yForHum(p.humidity) : null,
        valFn: (p) => p.humidity,
        strokeColor: this.colors.hum,
        fillStart: this.colors.humFillStart,
        fillEnd: this.colors.humFillEnd,
        lineWidth: 2.5,
        pBottom,
        pTop,
        pLeft,
        pRight,
      });
    }

    // 4. Draw Temperature Series (Area + Spline)
    if (showTemp) {
      this._drawSeries({
        ctx,
        points: this.data,
        xFn: (p) => xForTime(p.timestamp.getTime()),
        yFn: (p) => p.temperature != null ? yForTemp(p.temperature) : null,
        valFn: (p) => p.temperature,
        strokeColor: this.colors.temp,
        fillStart: this.colors.tempFillStart,
        fillEnd: this.colors.tempFillEnd,
        lineWidth: 3.2,
        pBottom,
        pTop,
        pLeft,
        pRight,
      });
    }

    // 5. Draw Interactive Crosshair & Highlight Dots
    if (this.activePointIndex !== null && this.activePointIndex < this.data.length) {
      const activePt = this.data[this.activePointIndex];
      const activeX = xForTime(activePt.timestamp.getTime());

      // Vertical crosshair line
      ctx.strokeStyle = this.colors.crosshair;
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(activeX, pTop);
      ctx.lineTo(activeX, pBottom);
      ctx.stroke();
      ctx.setLineDash([]);

      // Highlight dot for Humidity
      if (showHum && activePt.humidity != null) {
        const hy = yForHum(activePt.humidity);
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = this.colors.hum;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(activeX, hy, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }

      // Highlight dot for Temperature
      if (showTemp && activePt.temperature != null) {
        const ty = yForTemp(activePt.temperature);
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = this.colors.temp;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(activeX, ty, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }
    }
  }


  _drawSeries({ ctx, points, xFn, yFn, valFn, strokeColor, fillStart, fillEnd, lineWidth, pBottom, pTop, pLeft, pRight }) {
    // Extract valid contiguous segments (to gracefully handle gaps without invalid spikes)
    const segments = [];
    let currentSegment = [];

    for (let i = 0; i < points.length; i++) {
      const pt = points[i];
      if (valFn(pt) != null) {
        currentSegment.push({ x: xFn(pt), y: yFn(pt) });
      } else if (currentSegment.length > 0) {
        segments.push(currentSegment);
        currentSegment = [];
      }
    }
    if (currentSegment.length > 0) segments.push(currentSegment);

    for (const seg of segments) {
      if (seg.length === 0) continue;

      ctx.save();
      ctx.beginPath();
      ctx.rect(pLeft, pTop - 2, pRight - pLeft, (pBottom - pTop) + 4);
      ctx.clip();

      // 1. Draw gradient fill under the curve
      const gradient = ctx.createLinearGradient(0, pTop, 0, pBottom);
      gradient.addColorStop(0, fillStart);
      gradient.addColorStop(1, fillEnd);

      ctx.beginPath();
      ctx.moveTo(seg[0].x, pBottom);
      ctx.lineTo(seg[0].x, seg[0].y);

      for (let i = 0; i < seg.length - 1; i++) {
        const p0 = seg[i];
        const p1 = seg[i + 1];
        const cx = (p0.x + p1.x) / 2;
        ctx.bezierCurveTo(cx, p0.y, cx, p1.y, p1.x, p1.y);
      }

      ctx.lineTo(seg[seg.length - 1].x, pBottom);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();

      // 2. Draw line curve
      ctx.beginPath();
      ctx.moveTo(seg[0].x, seg[0].y);

      for (let i = 0; i < seg.length - 1; i++) {
        const p0 = seg[i];
        const p1 = seg[i + 1];
        const cx = (p0.x + p1.x) / 2;
        ctx.bezierCurveTo(cx, p0.y, cx, p1.y, p1.x, p1.y);
      }

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = lineWidth;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.stroke();

      ctx.restore();
    }
  }

  destroy() {
    if (this.resizeObserver) this.resizeObserver.disconnect();
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
  }
}

window.TelemetryChart = TelemetryChart;
