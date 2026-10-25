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
  $('#copy-prompt').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('#starter-prompt').textContent.trim());toast('绘图提示已复制');}catch{const r=document.createRange();r.selectNodeContents($('#starter-prompt'));const s=getSelection();s.removeAllRanges();s.addRange(r);toast('提示已选中，可手动复制');}});
  const chartDialog=$('#chart-dialog'),videoDialog=$('#video-dialog'),video=$('#demo-video');
  const charts=$$('.chart-card');
  const titles=Object.fromEntries(charts.map(card=>[card.dataset.chart,$('h3',card).textContent]));
  let mode='python',category='all',selectedChart='chord',release;
  const extension=()=>mode==='matlab'?'emf':'png';
  const format=()=>extension().toUpperCase();
  const modeLabel=()=>mode==='matlab'?'MATLAB / EMF':'Python / PNG';
  const original=slug=>`downloads/figures/${mode}/${slug}.${extension()}`;
  const preview=slug=>`assets/charts/${mode}-${slug}.webp`;
  function refreshDialog(){
    $('#lightbox-image').src=preview(selectedChart);$('#lightbox-image').alt=titles[selectedChart]+'，'+modeLabel()+'模式';
    $('#chart-dialog-title').textContent=titles[selectedChart];$('#dialog-mode-label').textContent=modeLabel().toUpperCase();
    $('#dialog-download').href=original(selectedChart);$('#dialog-download').textContent=`下载${format()}原图 ↘`;
    $('#dialog-source').href=`https://github.com/xiaonshen1031-eng/ProjectX/blob/main/gallery/build_${mode==='matlab'?'matlab.m':'python.py'}`;
  }
  function setMode(value){
    if(!['python','matlab'].includes(value))return;mode=value;
    $$('[data-mode]').forEach(b=>{const on=b.dataset.mode===mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});
    charts.forEach(card=>{const slug=card.dataset.chart;$('img',card).src=preview(slug);$('.chart-format',card).textContent=modeLabel().toUpperCase();const link=$('.chart-download',card);link.href=original(slug);link.textContent=format()+' ↘';link.setAttribute('aria-label',`下载${titles[slug]}${format()}原图`);});
    updateCount();if(chartDialog.open)refreshDialog();
  }
  function updateCount(){const count=charts.filter(c=>!c.hidden).length;$('#collection-status').textContent=`${modeLabel()} · ${count}类图型`;}
  $$('[data-mode]').forEach(button=>button.addEventListener('click',()=>setMode(button.dataset.mode)));
  $$('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=button.dataset.category;$$('[data-category]').forEach(b=>{const on=b===button;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));});charts.forEach(c=>c.hidden=category!=='all'&&c.dataset.family!==category);updateCount();}));
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
