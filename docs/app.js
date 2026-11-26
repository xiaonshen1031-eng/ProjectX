'use strict';

(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const visible = element => Boolean(element && element.getClientRects().length && getComputedStyle(element).visibility !== 'hidden');
  const focus = element => {
    if (visible(element) && !element.disabled) element.focus({preventScroll: true});
  };
  const setText = (element, text) => {
    if (element && element.textContent !== text) element.textContent = text;
  };
  const setSource = (element, path) => {
    if (element && element.getAttribute('src') !== path) element.setAttribute('src', path);
  };
  function readPreference(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  }
  function writePreference(key, value) {
    try { localStorage.setItem(key, value); } catch {}
  }

  document.documentElement.classList.add('js');
  const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
  let userReducesMotion = readPreference('projectx-reduced-motion') === 'true';
  const reducesMotion = () => userReducesMotion || motionQuery.matches;
  const scrollBehavior = () => reducesMotion() ? 'auto' : 'smooth';
  const motionButton = $('#motion-toggle');
  function updateMotion() {
    const reduced = reducesMotion();
    document.documentElement.classList.toggle('reduced-motion', reduced);
    document.body.classList.toggle('reduced-motion', reduced);
    if (!motionButton) return;
    motionButton.setAttribute('aria-pressed', String(reduced));
    motionButton.setAttribute('aria-disabled', String(motionQuery.matches));
    setText(motionButton, motionQuery.matches ? '跟随系统减少动效' : reduced ? '动效已减少' : '减少动效');
  }
  motionButton?.addEventListener('click', () => {
    if (motionQuery.matches) return;
    userReducesMotion = !userReducesMotion;
    writePreference('projectx-reduced-motion', String(userReducesMotion));
    updateMotion();
  });
  motionQuery.addEventListener('change', updateMotion);
  updateMotion();

  if ('IntersectionObserver' in window) {
    const reveal = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        reveal.unobserve(entry.target);
      }
    }), {threshold: 0.06});
    $$('.reveal').forEach(element => reveal.observe(element));
  } else {
    $$('.reveal').forEach(element => element.classList.add('visible'));
  }
  let progressFrame = 0;
  function updateProgress() {
    progressFrame = 0;
    const length = document.documentElement.scrollHeight - innerHeight;
    const progress = length > 0 ? Math.min(1, Math.max(0, scrollY / length)) : 0;
    document.documentElement.style.setProperty('--page-progress', progress);
  }
  function queueProgress() {
    if (!progressFrame) progressFrame = requestAnimationFrame(updateProgress);
  }
  addEventListener('scroll', queueProgress, {passive: true});
  addEventListener('resize', queueProgress);
  document.addEventListener('visibilitychange', () => document.body.classList.toggle('page-hidden', document.hidden));
  updateProgress();

  const menu = $('.menu-toggle');
  const navigation = $('#site-nav');
  if (menu && navigation) {
    const isOpen = () => menu.getAttribute('aria-expanded') === 'true';
    function setMenu(open, restoreFocus = false) {
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? '收起导航' : '展开导航');
      navigation.classList.toggle('open', open);
      if (open) focus($('a', navigation));
      else if (restoreFocus) focus(menu);
    }
    menu.addEventListener('click', () => setMenu(!isOpen(), isOpen()));
    navigation.addEventListener('click', event => {
      const link = event.target.closest('a');
      if (!link || !isOpen()) return;
      setMenu(false);
      if (link.hash && link.pathname === location.pathname && link.origin === location.origin) {
        const target = document.getElementById(link.hash.slice(1));
        if (target) {
          if (!target.hasAttribute('tabindex')) target.tabIndex = -1;
          focus(target);
        }
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && isOpen()) {
        event.preventDefault();
        setMenu(false, true);
      }
    });
    document.addEventListener('pointerdown', event => {
      if (isOpen() && !menu.contains(event.target) && !navigation.contains(event.target)) setMenu(false);
    });
    document.addEventListener('focusin', event => {
      if (isOpen() && !menu.contains(event.target) && !navigation.contains(event.target)) setMenu(false);
    });
    addEventListener('resize', () => {
      if (isOpen() && !visible(menu)) setMenu(false);
    });
  }

  let toastTimer;
  function toast(text) {
    const output = $('#toast');
    if (!output) return;
    setText(output, text);
    output.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => output.classList.remove('show'), 2400);
  }
  $('#copy-prompt')?.addEventListener('click', async () => {
    const prompt = $('#starter-prompt');
    if (!prompt) return;
    try {
      await navigator.clipboard.writeText(prompt.textContent.trim());
      toast('项目提示已复制');
    } catch {
      const selection = getSelection();
      if (!selection) return;
      const range = document.createRange();
      range.selectNodeContents(prompt);
      selection.removeAllRanges();
      selection.addRange(range);
      toast('已选中提示，可手动复制');
    }
  });

  function scrollTabIntoPanel(tab, panel) {
    if (!panel || !visible(tab)) return;
    const tabRect = tab.getBoundingClientRect();
    const panelRect = panel.getBoundingClientRect();
    const horizontal = panel.scrollWidth > panel.clientWidth;
    const vertical = panel.scrollHeight > panel.clientHeight;
    const dx = tabRect.left < panelRect.left ? tabRect.left - panelRect.left
      : Math.max(0, tabRect.right - panelRect.right);
    const dy = tabRect.top < panelRect.top ? tabRect.top - panelRect.top
      : Math.max(0, tabRect.bottom - panelRect.bottom);
    if ((horizontal && dx) || (vertical && dy)) {
      panel.scrollBy({left: horizontal ? dx : 0, top: vertical ? dy : 0, behavior: scrollBehavior()});
    }
  }
  function arrowIndex(key, index, count) {
    if (!count) return;
    if (key === 'Home') return 0;
    if (key === 'End') return count - 1;
    if (key === 'ArrowRight' || key === 'ArrowDown') return (index + 1) % count;
    if (key === 'ArrowLeft' || key === 'ArrowUp') return (index + count - 1) % count;
  }

  const stages = {
    task: ['SCOPE', '界定研究任务', '从任务书确认客户需要做哪项判断。把判断所需的工况和指标写成计算问题。', '任务书、客户模板', '确定据以决策的工况和指标', '待回答的工程问题'],
    data: ['INPUT DATA', '让数据对应模型时段', '按计算问题确定采样间隔。汇总功率曲线时保留相同时间边界，回算电量，核对变更时间尺度后的总量。', '原始时序、单位、设备参数', '核对缺测，统一时间尺度', '各时段的模型输入'],
    model: ['MODEL', '用运行条件确定可行范围', '以充电调度为例，每辆车的接入窗口限定了可以分配功率的时段。聚合后的充电功率还受变压器余量约束。', '接入窗口、负荷、设备容量', '定义功率变量和时段约束', '可求解的调度模型'],
    compute: ['RECOMPUTATION', '从分配结果回算约束', '将车辆的时段功率相加，再加上基础负荷，即可逐时查验变压器限值。按每辆车的功率序列积分，核对它实际获得的电量。', '逐车功率分配结果', '独立重建变压器负荷和车辆电量', '可比较的工况结果'],
    analysis: ['INTERPRETATION', '满载时段的调整条件', '10 时达到容量上限。已有充电量可否转移，取决于同一车辆的其他接入时段及同期容量余量。若八个时段的可供电量低于需求，时段调整后仍有电量缺口。', '各车排程、逐时容量余量', '核定其他接入时段的可转移电量', '可调整的排程与剩余缺口'],
    delivery: ['DELIVERABLES', '把计算依据交给客户', '在报告中把限制条件放在相关图表旁。计算脚本复现图上的数值，汇报页保留影响方案选择的工况。', '工程判断、客户模板', '编排报告并检查成稿页面', '技术报告、汇报和复算材料']
  };
  const stageTabs = $$('[data-stage]');
  const stagePanel = $('#workflow-detail');
  const stageFieldIds = ['workflow-step-label', 'workflow-step-title', 'workflow-step-body', 'workflow-input', 'workflow-process', 'workflow-output'];
  function showStage(tab, moveFocus = false) {
    if (!tab || !stagePanel) return;
    const content = stages[tab.dataset.stage];
    if (!content) return;
    stageTabs.forEach(button => {
      const active = button === tab;
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
    });
    stagePanel.setAttribute('aria-labelledby', tab.id);
    stageFieldIds.forEach((id, i) => setText(document.getElementById(id), content[i]));
    if (moveFocus) {
      focus(tab);
      scrollTabIntoPanel(tab, tab.closest('[role="tablist"]'));
    }
  }
  stageTabs.forEach((tab, index) => {
    tab.addEventListener('click', () => showStage(tab));
    tab.addEventListener('keydown', event => {
      const next = arrowIndex(event.key, index, stageTabs.length);
      if (next === undefined) return;
      event.preventDefault();
      showStage(stageTabs[next], true);
    });
  });
  $$('[data-route]').forEach(link => link.addEventListener('click', () => {
    showStage(stageTabs.find(tab => tab.dataset.stage === link.dataset.route));
  }));

  const chartDialog = $('#chart-dialog');
  const videoDialog = $('#video-dialog');
  const video = $('#demo-video');
  const openDialogs = new Set();
  let savedOverflow;
  function showDialog(dialog, opener) {
    if (!dialog || dialog.open) return;
    dialog.showModal();
    if (!openDialogs.size) {
      savedOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
    }
    openDialogs.add(dialog);
    dialog.openedBy = opener;
    focus($('[data-close]', dialog));
  }
  function restoreDialogFocus(dialog, backup) {
    const opener = visible(dialog.openedBy) ? dialog.openedBy : backup;
    dialog.openedBy = null;
    openDialogs.delete(dialog);
    if (!openDialogs.size) document.body.style.overflow = savedOverflow ?? '';
    focus(opener);
  }
  [chartDialog, videoDialog].filter(Boolean).forEach(dialog => {
    let pressedBackdrop = false;
    function outside(event) {
      const rect = dialog.getBoundingClientRect();
      return event.target === dialog && (
        event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom
      );
    }
    dialog.addEventListener('pointerdown', event => { pressedBackdrop = outside(event); });
    dialog.addEventListener('click', event => {
      if (pressedBackdrop && outside(event)) dialog.close();
      pressedBackdrop = false;
    });
    $$('[data-close]', dialog).forEach(button => button.addEventListener('click', () => dialog.close()));
  });

  const gallery = $('#gallery');
  const searchBox = $('#chart-search');
  const clearSearch = $('#clear-search');
  const emptyPanel = $('#atlas-empty');
  const zoomButton = $('#image-zoom');
  const dialogPicture = $('#lightbox-image');
  const dialogScroll = $('.chart-dialog-scroll');
  const categories = $$('[data-category]');
  const modeButtons = $$('[data-mode]');
  const languageButtons = $$('[data-lang]');
  const formatByMode = {python: 'PNG', matlab: 'EMF'};
  const modeName = {python: 'Python / PNG', matlab: 'MATLAB / EMF'};
  const languageName = {zh: '中文', en: '英文'};
  const familyName = {
    zh: {time: '时序与调度', distribution: '分布比较', relation: '关联与构成', space: '空间与约束', evaluation: '评估对比'},
    en: {time: 'Time and scheduling', distribution: 'Distributions', relation: 'Relations and composition', space: 'Space and constraints', evaluation: 'Evaluation'}
  };
  const searchKey = text => (text ?? '').normalize('NFKC').toLocaleLowerCase().trim();
  const charts = $$('.chart-card', gallery).map(card => {
    const {chart: id, family, pythonSource, matlabSource} = card.dataset;
    const metadata = {
      zh: {title: card.dataset.titleZh, description: card.dataset.descriptionZh, tags: card.dataset.tagsZh},
      en: {title: card.dataset.titleEn, description: card.dataset.descriptionEn, tags: card.dataset.tagsEn}
    };
    return {
      id, card, family, metadata, scripts: {python: pythonSource, matlab: matlabSource},
      title: $('h3', card), familyLabel: $('.chart-family', card), opener: $('[data-open]', card),
      image: $('img', card), download: $('.chart-download', card),
      search: searchKey([id.replaceAll('-', ' '), family, familyName.zh[family], familyName.en[family],
        ...Object.values(metadata.zh), ...Object.values(metadata.en)].join(' '))
    };
  });

  let mode = 'python';
  let language = readPreference('projectx-figure-language') === 'en' ? 'en' : 'zh';
  let selectedChart;
  let available = charts;
  let category = 'all';

  function figurePaths(chart) {
    const folder = language === 'zh' ? 'zh/' : '';
    return {
      thumbnail: 'assets/charts/' + folder + mode + '-' + chart.id + '.webp',
      original: 'downloads/figures/' + mode + '/' + folder + chart.id + '.' + formatByMode[mode].toLowerCase(),
      detail: 'assets/charts/detail/' + folder + 'matlab-' + chart.id + '.webp'
    };
  }
  function setPressed(buttons, key, selected) {
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset[key] === selected)));
  }
  function renderCard(chart) {
    const paths = figurePaths(chart);
    const {title} = chart.metadata[language];
    chart.card.lang = language === 'zh' ? 'zh-CN' : 'en';
    setText(chart.title, title);
    setText(chart.familyLabel, familyName[language][chart.family]);
    chart.opener.href = paths.original;
    chart.opener.setAttribute('aria-label', language === 'zh' ? '查看' + title + '大图' : 'View ' + title + ' full size');
    const format = formatByMode[mode];
    chart.download.href = paths.original;
    chart.download.download = chart.id + '-' + language + '.' + format.toLowerCase();
    setText(chart.download, format + ' ↓');
    chart.download.setAttribute('aria-label', language === 'zh' ? '下载' + title + '的中文 ' + format + ' 原图' : 'Download ' + title + ' as ' + format);
    setSource(chart.image, paths.thumbnail);
  }
  function renderDialog() {
    if (!chartDialog || !selectedChart) return;
    const {title, description} = selectedChart.metadata[language];
    const paths = figurePaths(selectedChart);
    const zoomed = chartDialog.classList.contains('is-zoomed');
    setSource(dialogPicture, zoomed ? (mode === 'python' ? paths.original : paths.detail) : paths.thumbnail);
    dialogPicture.alt = title;
    dialogPicture.lang = language === 'zh' ? 'zh-CN' : 'en';
    const heading = $('#chart-dialog-title');
    const reading = $('#dialog-reading');
    setText(heading, title);
    setText($('#dialog-note'), description);
    heading.lang = reading.lang = dialogPicture.lang;
    setText($('#dialog-mode-label'), languageName[language] + ' · ' + modeName[mode]);
    const download = $('#dialog-download');
    download.href = paths.original;
    download.download = selectedChart.id + '-' + language + '.' + formatByMode[mode].toLowerCase();
    setText(download, '下载' + languageName[language] + ' ' + formatByMode[mode] + ' ↘');
    $('#dialog-source').href = 'https://github.com/xiaonshen1031-eng/ProjectX/blob/main/gallery/' + selectedChart.scripts[mode];
    $('#dialog-backend').value = mode;
    $('#dialog-language').value = language;
    $$('[data-dialog-step]', chartDialog).forEach(button => button.disabled = available.length < 2);
  }
  function setZoom(on) {
    chartDialog?.classList.toggle('is-zoomed', on);
    zoomButton?.setAttribute('aria-pressed', String(on));
    setText(zoomButton, on ? '适合屏幕' : '放大查看');
    const hint = $('#zoom-hint');
    if (hint) hint.hidden = !on;
    if (dialogScroll) {
      dialogScroll.tabIndex = on ? 0 : -1;
      if (on) dialogScroll.setAttribute('aria-label', '图型大图，可滚动查看');
      else dialogScroll.removeAttribute('aria-label');
      dialogScroll.scrollTo(0, 0);
    }
  }
  function cycleChart(offset) {
    if (available.length < 2) return;
    const at = available.indexOf(selectedChart);
    selectedChart = available[(at + offset + available.length) % available.length];
    renderDialog();
    dialogScroll?.scrollTo(0, 0);
  }
  function applyFilters() {
    const query = searchKey(searchBox?.value).split(/\s+/).filter(Boolean);
    available = charts.filter(chart => (
      (category === 'all' || chart.family === category) && query.every(term => chart.search.includes(term))
    ));
    const visibleCharts = new Set(available);
    for (const chart of charts) {
      chart.card.hidden = !visibleCharts.has(chart);
      if (!chart.card.hidden) renderCard(chart);
    }
    if (emptyPanel) emptyPanel.hidden = Boolean(available.length);
    if (clearSearch) clearSearch.hidden = !searchBox?.value;
    setPressed(categories, 'category', category);
    setText($('#collection-status'), category === 'all' && !query.length ? '' : '找到 ' + available.length + ' 类图型');
    queueProgress();
  }
  function setMode(value) {
    if (value !== 'python' && value !== 'matlab') return;
    mode = value;
    setPressed(modeButtons, 'mode', mode);
    available.forEach(renderCard);
    if (chartDialog?.open) renderDialog();
  }
  function setLanguage(value) {
    if (value !== 'zh' && value !== 'en') return;
    language = value;
    setPressed(languageButtons, 'lang', language);
    available.forEach(renderCard);
    if (chartDialog?.open) renderDialog();
    writePreference('projectx-figure-language', language);
  }

  charts.forEach(chart => chart.opener.addEventListener('click', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (!chartDialog || typeof chartDialog.showModal !== 'function') return;
    event.preventDefault();
    selectedChart = chart;
    setZoom(false);
    renderDialog();
    showDialog(chartDialog, chart.opener);
  }));
  modeButtons.forEach(button => button.addEventListener('click', () => setMode(button.dataset.mode)));
  languageButtons.forEach(button => button.addEventListener('click', () => setLanguage(button.dataset.lang)));
  categories.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.category;
    applyFilters();
  }));
  searchBox?.addEventListener('input', applyFilters);
  clearSearch?.addEventListener('click', () => {
    searchBox.value = '';
    applyFilters();
    focus(searchBox);
  });
  $('#reset-atlas')?.addEventListener('click', () => {
    searchBox.value = '';
    category = 'all';
    applyFilters();
    focus(searchBox);
  });
  $('#dialog-backend')?.addEventListener('change', event => setMode(event.target.value));
  $('#dialog-language')?.addEventListener('change', event => setLanguage(event.target.value));
  $$('[data-use-mode]').forEach(button => button.addEventListener('click', () => {
    setMode(button.dataset.useMode);
    gallery?.scrollIntoView({behavior: scrollBehavior(), block: 'start'});
    focus(modeButtons.find(item => item.dataset.mode === mode));
  }));
  function toggleZoom() {
    if (!chartDialog) return;
    const on = !chartDialog.classList.contains('is-zoomed');
    setZoom(on);
    renderDialog();
    focus(on ? dialogScroll : zoomButton);
  }
  zoomButton?.addEventListener('click', toggleZoom);
  dialogPicture?.addEventListener('click', toggleZoom);
  $$('[data-dialog-step]').forEach(button => button.addEventListener('click', () => cycleChart(Number(button.dataset.dialogStep))));
  chartDialog?.addEventListener('keydown', event => {
    if (event.target.closest('select, input, textarea') || chartDialog.classList.contains('is-zoomed')) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      cycleChart(event.key === 'ArrowLeft' ? -1 : 1);
    }
  });
  chartDialog?.addEventListener('close', () => restoreDialogFocus(chartDialog, selectedChart?.opener || searchBox));
  if (charts.length) setLanguage(language);

  const versionPattern = /^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$/;
  const declaredVersion = $('[data-version]')?.textContent.trim().replace(/^v/, '');
  function validLocalFile(path, directory) {
    if (typeof path !== 'string' || !path.startsWith(directory)) return false;
    const resolved = new URL(path, document.baseURI);
    const permitted = new URL(directory, document.baseURI);
    return resolved.origin === permitted.origin && resolved.pathname.startsWith(permitted.pathname);
  }
  function releaseIsCurrent(version) {
    return versionPattern.test(version) && (
      !versionPattern.test(declaredVersion) || version.localeCompare(declaredVersion, undefined, {numeric: true}) >= 0
    );
  }
  function formatTime(seconds) {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = Math.floor(seconds % 60).toString().padStart(2, '0');
    return min + ':' + sec;
  }
  const release = fetch('release.json', {cache: 'no-cache'}).then(response => {
    if (!response.ok) return null;
    return response.json();
  }).then(data => {
    if (!data) return null;
    if (releaseIsCurrent(data.version) && validLocalFile(data.download, 'downloads/')) {
      $$('[data-version]').forEach(element => setText(element, 'v' + data.version));
      $$('[data-download]').forEach(element => element.href = data.download);
      if (Number.isFinite(data.bytes) && data.bytes > 0) {
        $$('[data-download-size]').forEach(element => setText(element, 'ZIP · ' + Math.round(data.bytes / 1024) + ' KiB'));
      }
      if (Number.isInteger(data.tests?.regressions) && data.tests.regressions >= 0) {
        $$('[data-test-count]').forEach(element => setText(element, String(data.tests.regressions)));
      }
    }
    if (!releaseIsCurrent(data.version)) return null;
    if (Number.isFinite(data.video?.duration) && data.video.duration > 0) {
      $$('[data-video-duration]').forEach(element => setText(element, formatTime(data.video.duration)));
    }
    if (Array.isArray(data.video?.chapters)) $$('[data-chapter]').forEach(button => {
      const chapter = data.video.chapters.find(item => item.id === button.dataset.chapter);
      if (Number.isFinite(chapter?.start) && chapter.start >= 0) setText($('span', button), formatTime(chapter.start));
    });
    return data;
  }).catch(() => null);

  let videoRequest = 0;
  let pendingSeek;
  function seekVideo() {
    if (videoDialog?.open && video.readyState >= 1 && Number.isFinite(pendingSeek)) {
      if (pendingSeek >= 0 && pendingSeek < video.duration) video.currentTime = pendingSeek;
      pendingSeek = undefined;
    }
  }
  function openVideo(button) {
    if (!video || !videoDialog) return;
    showDialog(videoDialog, button);
    const request = ++videoRequest;
    pendingSeek = button.dataset.chapter ? undefined : 0;
    seekVideo();
    if (button.dataset.chapter) {
      const fallback = Number.parseFloat(button.dataset.start);
      if (Number.isFinite(fallback)) {
        pendingSeek = fallback;
        seekVideo();
      } else {
        release.then(data => {
          if (!videoDialog.open || request !== videoRequest) return;
          pendingSeek = data?.video?.chapters?.find(chapter => chapter.id === button.dataset.chapter)?.start;
          seekVideo();
        });
      }
    }
    video.play()?.catch(() => {
      if (videoDialog.open && request === videoRequest) toast('点击视频播放按钮观看演示');
    });
  }
  video?.addEventListener('loadedmetadata', seekVideo);
  $$('.watch-video, [data-chapter]').forEach(button => button.addEventListener('click', () => openVideo(button)));
  videoDialog?.addEventListener('close', () => {
    videoRequest++;
    pendingSeek = undefined;
    video?.pause();
    restoreDialogFocus(videoDialog, $('.watch-video'));
  });
})();
