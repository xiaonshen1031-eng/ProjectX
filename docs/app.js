'use strict';
(() => {
  const $=(selector,root=document)=>root.querySelector(selector);
  const $$=(selector,root=document)=>[...root.querySelectorAll(selector)];
  document.documentElement.classList.add('js');
  const motionPreference=matchMedia('(prefers-reduced-motion: reduce)');
  let reduced=motionPreference.matches;
  try{reduced ||= localStorage.getItem('projectx-reduced-motion')==='true';}catch{}
  const motionButton=$('#motion-toggle');
  function applyMotion(){const active=reduced||motionPreference.matches;document.documentElement.classList.toggle('reduced-motion',active);document.body.classList.toggle('reduced-motion',active);motionButton.setAttribute('aria-pressed',String(active));motionButton.textContent=motionPreference.matches?'跟随系统减少动效':reduced?'动效已减少':'减少动效';}
  motionButton.addEventListener('click',()=>{if(motionPreference.matches)return;reduced=!reduced;applyMotion();try{localStorage.setItem('projectx-reduced-motion',String(reduced));}catch{}});
  motionPreference.addEventListener('change',applyMotion);applyMotion();
  const reveal=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');reveal.unobserve(e.target);}}),{threshold:.06});
  $$('.reveal').forEach(e=>reveal.observe(e));
  let queued=false;
  function progress(){const available=document.documentElement.scrollHeight-innerHeight;document.documentElement.style.setProperty('--page-progress',available>0?Math.min(1,Math.max(0,scrollY/available)):0);queued=false;}
  addEventListener('scroll',()=>{if(!queued){queued=true;requestAnimationFrame(progress);}},{passive:true});addEventListener('resize',progress);progress();
  document.addEventListener('visibilitychange',()=>document.body.classList.toggle('page-hidden',document.hidden));
  const menu=$('.menu-toggle'),nav=$('#site-nav');
  function closeMenu(){menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','展开导航');nav.classList.remove('open');}
  menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'收起导航':'展开导航');nav.classList.toggle('open',open);});
  $$('a',nav).forEach(a=>a.addEventListener('click',closeMenu));
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&nav.classList.contains('open')){closeMenu();menu.focus();}});
  const art=$('.hero-art'),stage=$('.art-stage');
  new ResizeObserver(entries=>entries.forEach(e=>art.style.setProperty('--art-scale',String(e.contentRect.width/640)))).observe(art);
  art.addEventListener('pointermove',event=>{if(reduced||motionPreference.matches||!matchMedia('(pointer:fine)').matches)return;const r=art.getBoundingClientRect();stage.style.setProperty('--pointer-x',`${((event.clientX-r.left)/r.width-.5)*10}px`);stage.style.setProperty('--pointer-y',`${((event.clientY-r.top)/r.height-.5)*8}px`);});
  art.addEventListener('pointerleave',()=>{stage.style.setProperty('--pointer-x','0px');stage.style.setProperty('--pointer-y','0px');});
  let toastTimer;
  function toast(text){const el=$('#toast');el.textContent=text;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),2300);}
  $('#copy-prompt').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('#starter-prompt').textContent.trim());toast('项目提示已复制');}catch{const r=document.createRange();r.selectNodeContents($('#starter-prompt'));const s=getSelection();s.removeAllRanges();s.addRange(r);toast('提示已选中，可手动复制');}});
  const stages={
    task:['01 / TASK & MATERIALS','先明确，这个项目要解决什么。','从任务书、合同研究内容和已有材料中找到研究对象、承担范围与交付要求，再把要求拆成相互衔接的技术问题。','任务书、合同内容、已有成果与客户模板','拆解任务，确定研究对象、问题与承担范围','研究问题、工作边界与交付清单'],
    data:['02 / DATA & ADAPTATION','把数据，整理成模型输入。','检查字段、单位、时间尺度和缺失情况，按照研究对象组织数据。需要跨地区或场景适配时，结合当地规模与约束调整曲线，并核查聚合前后的总量关系。','原始表格、时序曲线、公开数据与地区规模','数据清理、时间对齐、尺度适配与总量核查','模型输入、参数表与处理脚本'],
    model:['03 / MODEL & METHOD','把问题，写成有联系的模型。','围绕输入、输出和需要回答的问题，明确变量、目标与运行约束。参考相关方法建立模型，说明关键关系如何影响结果，再选择适合的计算方法。','研究问题、数据输入、物理关系与参考方法','定义变量、目标和约束，建立模型关系','数学模型、方法选择与可计算的表达'],
    compute:['04 / COMPUTE & VALIDATE','完成计算，再核查结果是否成立。','实施求解、预测或仿真，用相同数据划分、参数条件与指标组织比较。结合约束残差、独立计算和边界条件检查，定位异常并修正模型或实现。','模型、数据、参数设置与比较方案','求解计算、公平比较、独立复核与异常修正','计算结果、比较指标与可复算代码'],
    analysis:['05 / RESULTS & ANALYSIS','从结果变化，解释背后的原因。','先比较总体差异，再追踪时间、空间、场景和参数变化。选择能够呈现这些关系的图表，把数值、模型机制与工程含义连成完整分析。','计算结果、比较方案与研究问题','差异比较、时空分析、敏感性分析与图表表达','有依据的结论、结果图表与连续分析'],
    delivery:['06 / DELIVERABLES','沿客户模板，把成果交付完整。','把建模、结果和分析整理成技术报告，再转化为适合汇报的PPT。检查公式、图表、参考文献和页面，连同数据处理与计算源码一起交付。','模型关系、计算结果、分析与客户模板','报告写作、模板汇报、公式处理与页面检查','技术报告、PPT、图件与计算材料']
  };
  const stageTabs=$$('[data-stage]');
  function showStage(button,focus=false){
    const content=stages[button.dataset.stage];
    stageTabs.forEach(tab=>{const active=tab===button;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
    $('#workflow-detail').setAttribute('aria-labelledby',button.id);
    ['workflow-step-label','workflow-step-title','workflow-step-body','workflow-input','workflow-process','workflow-output'].forEach((id,i)=>$('#'+id).textContent=content[i]);
    if(focus)button.focus({preventScroll:true});
  }
  stageTabs.forEach((button,i)=>{
    button.addEventListener('click',()=>showStage(button));
    button.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(i+1)%stageTabs.length;if(event.key==='ArrowLeft')next=(i+stageTabs.length-1)%stageTabs.length;if(event.key==='Home')next=0;if(event.key==='End')next=stageTabs.length-1;if(next!==undefined){event.preventDefault();showStage(stageTabs[next],true);}});
  });
  const chartDialog=$('#chart-dialog'),videoDialog=$('#video-dialog'),video=$('#demo-video');
  const charts=$$('.chart-card');
  const titles=Object.fromEntries(charts.map(card=>[card.dataset.chart,$('h3',card).textContent]));
  let mode='python',category='all',expanded=false,selectedChart='gantt',release;
  const extension=()=>mode==='matlab'?'emf':'png';
  const format=()=>extension().toUpperCase();
  const modeLabel=()=>mode==='matlab'?'MATLAB / EMF':'Python / PNG';
  const original=slug=>`downloads/figures/${mode}/${slug}.${extension()}`;
  const preview=slug=>`assets/charts/${mode}-${slug}.webp`;
  function refreshDialog(){
    $('#lightbox-image').src=preview(selectedChart);$('#lightbox-image').alt=titles[selectedChart]+'，'+modeLabel()+'模式';
    $('#chart-dialog-title').textContent=titles[selectedChart];$('#dialog-mode-label').textContent=modeLabel().toUpperCase();
    $('#dialog-download').href=original(selectedChart);$('#dialog-download').textContent=`下载${format()}原图 ↘`;
    const extra=charts.find(c=>c.dataset.chart===selectedChart).dataset.extra==='true'?'_extra':'';
    $('#dialog-source').href=`https://github.com/xiaonshen1031-eng/ProjectX/blob/main/gallery/build_${mode}${extra}.${mode==='matlab'?'m':'py'}`;
  }
  function setMode(value){
    if(!['python','matlab'].includes(value))return;mode=value;
    $$('[data-mode]').forEach(b=>{const on=b.dataset.mode===mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
    charts.forEach(card=>{const slug=card.dataset.chart;$('img',card).src=preview(slug);$('.chart-format',card).textContent=modeLabel().toUpperCase();const link=$('.chart-download',card);link.href=original(slug);link.textContent=format()+' ↘';link.setAttribute('aria-label',`下载${titles[slug]}${format()}原图`);});
    updateCount();if(chartDialog.open)refreshDialog();
  }
  function updateCount(){const count=charts.filter(c=>!c.hidden).length;const prefix=category==='all'&&!expanded?'精选':'';$('#collection-status').textContent=`${modeLabel()} · ${prefix}${count}类 / 共${charts.length}类图型`;}
  function filterCharts(){
    charts.forEach(c=>c.hidden=category==='all'?(!expanded&&c.dataset.featured!=='true'):c.dataset.family!==category);
    const more=$('#expand-gallery');more.parentElement.hidden=category!=='all';more.setAttribute('aria-expanded',String(expanded));more.innerHTML=expanded?'收起，查看精选6类 <span aria-hidden="true">−</span>':`展开全部${charts.length}类图型 <span aria-hidden="true">＋</span>`;updateCount();requestAnimationFrame(progress);
  }
  $$('[data-mode]').forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.mode)));
  $$('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=button.dataset.category;$$('[data-category]').forEach(b=>{const on=b===button;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});filterCharts();$('.gallery-toolbar').scrollIntoView({block:'start',behavior:'instant'});}));
  $('#expand-gallery').addEventListener('click',()=>{expanded=!expanded;filterCharts();if(!expanded)$('#gallery').scrollIntoView({behavior:reduced?'auto':'smooth'});});
  $$('[data-use-mode]').forEach(button=>button.addEventListener('click',()=>{setMode(button.dataset.useMode);$('#gallery').scrollIntoView({behavior:reduced?'auto':'smooth'});$('.mode-switch [data-mode="'+mode+'"]').focus({preventScroll:true});}));
  $$('[data-open]').forEach(button=>button.addEventListener('click',()=>{selectedChart=button.dataset.open;refreshDialog();chartDialog.classList.remove('is-zoomed');$('#image-zoom').setAttribute('aria-pressed','false');$('#image-zoom').textContent='放大原图';chartDialog.showModal();document.body.style.overflow='hidden';}));
  $('#image-zoom').addEventListener('click',()=>{const active=chartDialog.classList.toggle('is-zoomed');$('#image-zoom').setAttribute('aria-pressed',String(active));$('#image-zoom').textContent=active?'适合屏幕':'放大原图';});
  function openVideo(start){
    if(!videoDialog.open)videoDialog.showModal();document.body.style.overflow='hidden';
    if(Number.isFinite(start)){if(video.readyState>=1)video.currentTime=start;else video.addEventListener('loadedmetadata',()=>{video.currentTime=start;},{once:true});}
    const playing=video.play();if(playing)playing.catch(()=>toast('点击视频播放按钮观看演示'));
  }
  $$('.watch-video').forEach(b=>b.addEventListener('click',()=>openVideo()));
  $$('[data-chapter]').forEach(b=>b.addEventListener('click',()=>{const chapter=release?.video?.chapters?.find(c=>c.id===b.dataset.chapter);openVideo(chapter?.start||0);}));
  $$('[data-close]').forEach(b=>b.addEventListener('click',()=>$('#'+b.dataset.close).close()));
  [chartDialog,videoDialog].forEach(dialog=>{
    dialog.addEventListener('close',()=>{if(dialog===videoDialog)video.pause();document.body.style.overflow='';});
    dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();});
  });
  const time=seconds=>`${Math.floor(seconds/60).toString().padStart(2,'0')}:${Math.floor(seconds%60).toString().padStart(2,'0')}`;
  fetch('release.json').then(r=>{if(!r.ok)throw Error('metadata');return r.json();}).then(r=>{release=r;$$('[data-version]').forEach(e=>e.textContent='v'+r.version);$$('[data-download-size]').forEach(e=>e.textContent=`ZIP · ${Math.round(r.bytes/1024)} KiB`);$$('[data-download]').forEach(e=>e.href=r.download);$$('[data-video-duration]').forEach(e=>e.textContent=time(r.video.duration));$$('[data-chapter]').forEach(b=>{const c=r.video.chapters.find(c=>c.id===b.dataset.chapter);if(c)$('span',b).textContent=time(c.start);});}).catch(()=>{});
})();
