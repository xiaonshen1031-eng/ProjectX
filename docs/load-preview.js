'use strict';

(() => {
  const canvas = document.querySelector('#load-plot');
  const range = document.querySelector('#load-period');
  const time = document.querySelector('#load-time');
  const loadValue = document.querySelector('#load-value');
  const marginValue = document.querySelector('#margin-value');
  const state = document.querySelector('#load-state');
  if (!canvas || !range) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Eight hourly values from the skill's synthetic allocation example.
  const limit = 55;
  const base = [0, 18, 25, 31, 36, 33, 24, 16];
  const load = [0, 51, 55, 53, 38, 33, 31, 22];
  const steps = load.length;
  const inset = { left: 33, right: 14, top: 15, bottom: 26 };
  const clock = index => String(index + 8).padStart(2, '0') + ':00';
  let current = Number(range.value);

  function rgbStop(gradient, first, last) {
    gradient.addColorStop(0, first);
    gradient.addColorStop(1, last);
    return gradient;
  }

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
    const x = index => left + (right - left) * index / (steps - 1);
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
      ctx.moveTo(x(0), y(values[0]));
      for (let i = 1; i < steps; i++) {
        const edge = (x(i - 1) + x(i)) / 2;
        ctx.lineTo(edge, y(values[i - 1]));
        ctx.lineTo(edge, y(values[i]));
        ctx.lineTo(x(i), y(values[i]));
      }
    }

    ctx.beginPath();
    stepped(load);
    ctx.lineTo(right, bottom);
    ctx.lineTo(left, bottom);
    ctx.closePath();
    ctx.fillStyle = rgbStop(ctx.createLinearGradient(0, inset.top, 0, bottom), '#6be6ff66', '#78c2ff03');
    ctx.fill();

    ctx.beginPath();
    stepped(base);
    ctx.lineWidth = 1.7;
    ctx.strokeStyle = '#adbaff';
    ctx.stroke();
    ctx.beginPath();
    stepped(load);
    ctx.lineWidth = 2.4;
    ctx.strokeStyle = '#7fe7ff';
    ctx.stroke();

    ctx.lineWidth = 1;
    ctx.strokeStyle = '#b4eaff7a';
    ctx.beginPath();
    ctx.moveTo(x(current), inset.top);
    ctx.lineTo(x(current), bottom + 3);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x(current), y(load[current]), 9, 0, Math.PI * 2);
    ctx.fillStyle = '#7fe7ff38';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x(current), y(load[current]), 4.3, 0, Math.PI * 2);
    ctx.fillStyle = '#f5fbff';
    ctx.fill();
    ctx.strokeStyle = '#68ddff';
    ctx.stroke();

    for (const i of [0, 2, 4, 7]) {
      ctx.fillStyle = '#d7e5ff';
      ctx.textAlign = i === 0 ? 'left' : i === steps - 1 ? 'right' : 'center';
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
    marginValue.firstChild.textContent = String(margin) + ' ';
    state.textContent = margin === 0 ? '达到上限' : '仍有余量';
    draw();
  }

  range.addEventListener('input', () => setPeriod(Number(range.value)));
  canvas.addEventListener('click', event => {
    const width = canvas.getBoundingClientRect().width - inset.left - inset.right;
    if (width > 0) setPeriod(Math.round((event.offsetX - inset.left) / width * (steps - 1)));
  });
  const resize = new ResizeObserver(draw);
  resize.observe(canvas);
  document.fonts.ready.then(draw);
  draw();
})();
