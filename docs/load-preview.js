'use strict';

(() => {
  const canvas = document.querySelector('#load-plot');
  const range = document.querySelector('#load-period');
  const time = document.querySelector('#load-time');
  const loadValue = document.querySelector('#load-value');
  const chargingValue = document.querySelector('#charging-value');
  const marginValue = document.querySelector('#margin-value');
  const summary = document.querySelector('#load-summary');
  if (!canvas || !range) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Eight hourly values from the skill's synthetic allocation example.
  const limit = 55;
  const base = [0, 18, 25, 31, 36, 33, 24, 16];
  const load = [0, 51, 55, 53, 38, 33, 31, 22];
  const steps = load.length;
  const inset = { left: 33, right: 14, top: 15, bottom: 26 };
  const colors = { load: '#f0f5ff', base: '#8ba9f9', fill: '#627fe75c', limit: '#d6e2ff', bound: '#f3c329' };
  const clock = index => String(index + 8).padStart(2, '0') + ':00';
  let current = Number(range.value);

  function draw() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const pixels = [Math.round(width * dpr), Math.round(height * dpr)];
    if (canvas.width !== pixels[0] || canvas.height !== pixels[1]) {
      canvas.width = pixels[0];
      canvas.height = pixels[1];
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    const left = inset.left;
    const right = width - inset.right;
    const bottom = height - inset.bottom;
    const slot = (right - left) / steps;
    const x = index => left + slot * (index + .5);
    const y = value => bottom - (bottom - inset.top) * value / 64;

    ctx.font = '11px Manrope, sans-serif';
    ctx.lineWidth = 1;
    ctx.textAlign = 'end';
    ctx.textBaseline = 'middle';
    for (const label of [0, 20, 40, limit]) {
      ctx.strokeStyle = label === limit ? '#dce9ffb0' : '#aac8ff35';
      ctx.setLineDash(label === limit ? [5, 5] : []);
      ctx.beginPath();
      ctx.moveTo(left, y(label));
      ctx.lineTo(right, y(label));
      ctx.stroke();
      ctx.fillStyle = '#d7e5ff';
      ctx.fillText(String(label), left - 7, y(label));
    }
    ctx.setLineDash([]);
    ctx.textAlign = 'left';
    ctx.fillText('kW', 1, 9);

    function stepped(values) {
      ctx.moveTo(left, y(values[0]));
      for (let i = 0; i < steps; i++) {
        const edge = left + slot * (i + 1);
        ctx.lineTo(edge, y(values[i]));
        if (i < steps - 1) ctx.lineTo(edge, y(values[i + 1]));
      }
    }

    ctx.fillStyle = '#d0ddff13';
    ctx.fillRect(left + current * slot, inset.top, slot, bottom - inset.top);
    ctx.fillStyle = colors.fill;
    load.forEach((value, index) => {
      ctx.fillRect(left + index * slot, y(value), slot, y(base[index]) - y(value));
    });

    ctx.beginPath();
    stepped(base);
    ctx.lineWidth = 1.7;
    ctx.strokeStyle = colors.base;
    ctx.stroke();
    ctx.beginPath();
    stepped(load);
    ctx.lineWidth = 2.2;
    ctx.strokeStyle = colors.load;
    ctx.stroke();

    const marker = x(current);
    if (load[current] < limit) {
      ctx.lineWidth = 1.4;
      ctx.strokeStyle = colors.limit;
      ctx.beginPath();
      ctx.moveTo(marker - 4, y(limit)); ctx.lineTo(marker + 4, y(limit));
      ctx.moveTo(marker, y(limit)); ctx.lineTo(marker, y(load[current]));
      ctx.stroke();
    }
    ctx.beginPath();
    if (load[current] === limit) {
      const level = y(limit);
      ctx.moveTo(marker, level - 5); ctx.lineTo(marker + 5, level);
      ctx.lineTo(marker, level + 5); ctx.lineTo(marker - 5, level);
      ctx.closePath();
      ctx.fillStyle = colors.bound;
    } else {
      ctx.arc(marker, y(load[current]), 4, 0, Math.PI * 2);
      ctx.fillStyle = colors.load;
    }
    ctx.fill();
    ctx.strokeStyle = '#172b6d';
    ctx.stroke();

    for (const i of [0, 2, 4, 7]) {
      ctx.fillStyle = '#d7e5ff';
      ctx.textAlign = 'center';
      ctx.fillText(clock(i), x(i), bottom + 15);
    }
  }

  function setPeriod(value) {
    const next = Math.max(0, Math.min(steps - 1, value));
    if (next === current) return;
    current = next;
    range.value = String(next);
    range.style.setProperty('--period-progress', (next * 100 / (steps - 1)).toFixed(2) + '%');
    const selectedTime = clock(next);
    const margin = limit - load[next];
    time.value = selectedTime;
    range.setAttribute('aria-valuetext', selectedTime);
    loadValue.firstChild.textContent = String(load[next]) + ' ';
    chargingValue.firstChild.textContent = String(load[next] - base[next]) + ' ';
    marginValue.firstChild.textContent = String(margin) + ' ';
    summary.classList.toggle('at-limit', margin === 0);
    draw();
  }

  range.addEventListener('input', () => setPeriod(Number(range.value)));
  canvas.addEventListener('click', event => {
    const width = canvas.getBoundingClientRect().width - inset.left - inset.right;
    if (width > 0) setPeriod(Math.floor((event.offsetX - inset.left) / width * steps));
  });
  const resize = new ResizeObserver(draw);
  resize.observe(canvas);
  document.fonts.ready.then(draw);
  draw();
})();
