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
    task: ['01 / TASK & MATERIALS', '确定项目要解决的问题', '从任务书、合同和已有成果确认承担范围，再把研究要求拆成可核查的问题。', '任务书、已有成果、客户模板', '核对研究对象、交付范围及约束', '技术问题和交付清单'],
    data: ['02 / DATA & ADAPTATION', '整理模型所需的数据', '核对字段、单位、时段及样本覆盖。曲线需要迁移到其他地区时，按当地规模调整，再校核总量。', '原始表格、历史曲线、地区规模', '清理数据，统一时段和统计单位', '模型输入、参数表、处理脚本'],
    model: ['03 / MODEL & METHOD', '建立能回答问题的模型', '确定输入、变量和运行约束。用已有物理关系或可验证的统计关系解释输出如何形成，再选择计算方法。', '工程问题和数据输入', '建立变量关系、边界和目标', '可计算的模型'],
    compute: ['04 / COMPUTE & VALIDATE', '复算关键约束', '在相同信息条件下比较各方案。从保存的结果重算约束残差，核对异常是来自输入、模型还是实现。', '模型、参数和对照方案', '求解并独立复核关键约束', '结果、比较指标和复算代码'],
    analysis: ['05 / RESULTS & ANALYSIS', '解释差异怎样产生', '在相同工况下比较结果。用曲线、配对差值或阈值定位变化，再说明哪个约束限制了可用能力。', '计算结果与对照工况', '定位差异，解释运行约束', '结果图表和工程判断'],
    delivery: ['06 / DELIVERABLES', '按客户模板交付', '把方法、工况和可复算结果编入技术报告。汇报页呈现决定方案的关键证据，并复核公式、图表和页面。', '结果、分析与客户模板', '编排报告，按实际页面复核', '报告、汇报、图件和源码']
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
  const atlasPicker = $('.atlas-picker');
  const mobilePicker = $('#mobile-chart-picker');
  const searchBox = $('#chart-search');
  const clearSearch = $('#clear-search');
  const resetAtlas = $('#reset-atlas');
  const emptyPanel = $('#atlas-empty');
  const status = $('#collection-status');
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
  const galleryTabs = new Map($$('[data-pick]').map(tab => [tab.dataset.pick, tab]));
  const searchKey = text => (text ?? '').normalize('NFKC').toLocaleLowerCase().trim();
  const charts = $$('.chart-card').map(card => {
    const {chart: id, family, extra} = card.dataset;
    const tab = galleryTabs.get(id);
    const metadata = {
      zh: {title: card.dataset.titleZh || $('h3', card)?.textContent, description: card.dataset.descriptionZh, tags: card.dataset.tagsZh},
      en: {title: card.dataset.titleEn, description: card.dataset.descriptionEn, tags: card.dataset.tagsEn}
    };
    return {
      id, card, tab, family, extra,
      title: $('h3', card), description: $('figcaption > p', card), tags: $('.chart-tags', card),
      opener: $('[data-open]', card), image: $('img', card), format: $('.chart-format', card), download: $('.chart-download', card),
      metadata,
      search: searchKey([id, family, familyName.zh[family], familyName.en[family], ...Object.values(metadata.zh), ...Object.values(metadata.en)].join(' '))
    };
  });

  let mode = 'python';
  const savedLanguage = readPreference('projectx-figure-language');
  let language = savedLanguage === 'en' ? 'en' : 'zh';
  let selectedChart = charts.find(chart => !chart.card.hidden) ?? charts[0];
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
    buttons.forEach(button => {
      const active = button.dataset[key] === selected;
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('active', active);
    });
  }
  function renderCard(chart) {
    const paths = figurePaths(chart);
    const {title, description, tags} = chart.metadata[language];
    const label = language === 'zh' ? '查看' + title + '大图' : 'View ' + title + ' full size';
    chart.card.dataset.figureLang = language;
    chart.card.lang = language === 'zh' ? 'zh-CN' : 'en';
    setText(chart.title, title);
    setText(chart.description, description);
    setText(chart.tags, tags);
    setText(chart.format, modeName[mode]);
    chart.opener?.setAttribute('aria-label', label);
    if (chart.image) chart.image.alt = language === 'zh' ? title + '，中文图' : title + ' — English figure';
    if (chart.download) {
      chart.download.href = paths.original;
      chart.download.download = chart.id + '-' + language + '.' + formatByMode[mode].toLowerCase();
      setText(chart.download, (language === 'zh' ? '中文 ' : 'EN ') + formatByMode[mode] + ' ↘');
      chart.download.setAttribute('aria-label', '下载' + languageName[language] + title + formatByMode[mode] + '原图');
    }
    // Hidden cards keep their image requests deferred until selection.
    if (chart === selectedChart) setSource(chart.image, paths.thumbnail);
  }
  function renderTab(chart) {
    if (!chart.tab) return;
    chart.tab.lang = language === 'zh' ? 'zh-CN' : 'en';
    setText($('strong', chart.tab), chart.metadata[language].title);
    setText($('small', chart.tab), familyName[language][chart.family]);
  }
  function renderStatus() {
    if (available.length) {
      const number = available.indexOf(selectedChart) + 1;
      setText(status, number + ' / ' + available.length + ' 类图型 · ' + languageName[language] + ' · ' + modeName[mode]);
    } else {
      setText(status, '没有匹配的图型');
    }
    $$('#chart-prev, #chart-next, [data-dialog-step]').forEach(button => button.disabled = available.length < 2);
  }
  function fillMobilePicker() {
    if (!mobilePicker) return;
    const options = available.map(chart => new Option(chart.metadata[language].title, chart.id));
    mobilePicker.replaceChildren(...options);
    mobilePicker.lang = language === 'zh' ? 'zh-CN' : 'en';
    mobilePicker.value = selectedChart?.id || '';
    mobilePicker.disabled = !available.length;
  }
  function renderDialog() {
    if (!chartDialog || !selectedChart) return;
    const {title} = selectedChart.metadata[language];
    const paths = figurePaths(selectedChart);
    const zoomed = chartDialog.classList.contains('is-zoomed');
    setSource(dialogPicture, zoomed ? (mode === 'python' ? paths.original : paths.detail) : paths.thumbnail);
    if (dialogPicture) dialogPicture.alt = title + '，' + languageName[language] + '，' + modeName[mode];
    chartDialog.dataset.figureLang = language;
    const heading = $('#chart-dialog-title');
    setText(heading, title);
    if (heading) heading.lang = language === 'zh' ? 'zh-CN' : 'en';
    setText($('#dialog-mode-label'), languageName[language] + ' · ' + modeName[mode]);
    const download = $('#dialog-download');
    if (download) {
      download.href = paths.original;
      download.download = selectedChart.id + '-' + language + '.' + formatByMode[mode].toLowerCase();
      setText(download, '下载' + languageName[language] + formatByMode[mode] + '原图 ↘');
    }
    const source = $('#dialog-source');
    if (source) {
      const script = mode === 'python' ? 'build_bilingual.py' : selectedChart.extra === 'true' ? 'build_matlab_extra.m' : 'build_matlab.m';
      source.href = 'https://github.com/xiaonshen1031-eng/ProjectX/blob/main/gallery/' + script;
    }
    const backend = $('#dialog-backend');
    const locale = $('#dialog-language');
    if (backend) backend.value = mode;
    if (locale) locale.value = language;
  }
  function selectChart(chart, moveFocus = false) {
    selectedChart = chart;
    for (const item of charts) {
      const active = chart === item;
      item.card.hidden = !active;
      item.card.classList.toggle('is-selected', active);
      if (item.tab) {
        item.tab.setAttribute('aria-selected', String(active));
        item.tab.tabIndex = active ? 0 : -1;
      }
    }
    if (chart) {
      renderCard(chart);
      if (moveFocus) focus(chart.tab);
      scrollTabIntoPanel(chart.tab, atlasPicker);
    }
    if (mobilePicker) mobilePicker.value = chart?.id || '';
    if (emptyPanel) emptyPanel.hidden = Boolean(chart);
    renderStatus();
    if (chartDialog?.open) {
      renderDialog();
      dialogScroll?.scrollTo(0, 0);
    }
    queueProgress();
  }
  function setZoom(on) {
    chartDialog?.classList.toggle('is-zoomed', on);
    zoomButton?.setAttribute('aria-pressed', String(on));
    setText(zoomButton, on ? '适合屏幕' : '放大查看');
    if (dialogScroll) {
      dialogScroll.tabIndex = on ? 0 : -1;
      if (on) dialogScroll.setAttribute('aria-label', '图型大图，可滚动查看');
      else dialogScroll.removeAttribute('aria-label');
      dialogScroll.scrollTo(0, 0);
    }
  }
  function cycleChart(offset, moveFocus = false) {
    if (available.length < 2) return;
    const at = available.indexOf(selectedChart);
    selectChart(available[(at + offset + available.length) % available.length], moveFocus);
  }
  function applyFilters() {
    const query = searchKey(searchBox?.value).split(/\s+/).filter(Boolean);
    available = charts.filter(chart => {
      return (category === 'all' || chart.family === category) && query.every(term => chart.search.includes(term));
    });
    for (const chart of charts) if (chart.tab) chart.tab.hidden = !available.includes(chart);
    setPressed(categories, 'category', category);
    if (clearSearch) clearSearch.hidden = !searchBox?.value;
    fillMobilePicker();
    selectChart(available.includes(selectedChart) ? selectedChart : available[0]);
  }
  function setMode(value) {
    if (value !== 'python' && value !== 'matlab') return;
    mode = value;
    setPressed(modeButtons, 'mode', mode);
    if (selectedChart) renderCard(selectedChart);
    renderStatus();
    if (chartDialog?.open) renderDialog();
  }
  function setLanguage(value) {
    if (value !== 'zh' && value !== 'en') return;
    language = value;
    setPressed(languageButtons, 'lang', language);
    if (atlasPicker) atlasPicker.dataset.figureLang = language;
    if (gallery) gallery.dataset.figureLang = language;
    charts.forEach(renderTab);
    fillMobilePicker();
    if (selectedChart) renderCard(selectedChart);
    renderStatus();
    if (chartDialog?.open) renderDialog();
    writePreference('projectx-figure-language', language);
  }

  charts.forEach(chart => {
    chart.tab?.addEventListener('click', () => selectChart(chart));
    chart.tab?.addEventListener('keydown', event => {
      const next = arrowIndex(event.key, available.indexOf(chart), available.length);
      if (next === undefined) return;
      event.preventDefault();
      selectChart(available[next], true);
    });
    chart.opener?.addEventListener('click', () => {
      selectChart(chart);
      setZoom(false);
      renderDialog();
      showDialog(chartDialog, chart.opener);
    });
  });
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
  resetAtlas?.addEventListener('click', () => {
    if (searchBox) searchBox.value = '';
    category = 'all';
    applyFilters();
    focus(searchBox ?? (visible(mobilePicker) ? mobilePicker : selectedChart?.tab));
  });
  mobilePicker?.addEventListener('change', event => {
    const chart = available.find(item => item.id === event.target.value);
    if (chart) selectChart(chart);
  });
  $('#chart-prev')?.addEventListener('click', () => cycleChart(-1));
  $('#chart-next')?.addEventListener('click', () => cycleChart(1));
  $('#dialog-backend')?.addEventListener('change', event => setMode(event.target.value));
  $('#dialog-language')?.addEventListener('change', event => setLanguage(event.target.value));
  $$('[data-use-mode]').forEach(button => button.addEventListener('click', () => {
    setMode(button.dataset.useMode);
    gallery?.scrollIntoView({behavior: scrollBehavior(), block: 'start'});
    focus(modeButtons.find(item => item.dataset.mode === mode));
  }));
  function toggleZoom() {
    if (!chartDialog) return;
    setZoom(!chartDialog.classList.contains('is-zoomed'));
    renderDialog();
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
  if (charts.length) {
    setLanguage(language);
    setMode(mode);
    applyFilters();
  }

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
