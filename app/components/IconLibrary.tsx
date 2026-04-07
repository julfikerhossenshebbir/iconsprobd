'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type { Category } from '@/lib/icons';

interface IconItem { name: string; body: string; }

interface Props {
  iconList: IconItem[];
  iconW: number;
  iconH: number;
  prefix: string;
  totalCount: number;
  categories: Record<string, Category>;
}

/* ── tiny helpers ─────────────────────────────── */
function hsvToHex(h: number, s: number, v: number): string {
  const i = Math.floor(h / 60) % 6;
  const f = h / 60 - Math.floor(h / 60);
  const p = v * (1 - s), q = v * (1 - f * s), t = v * (1 - (1 - f) * s);
  const rgb = [[v,t,p],[q,v,p],[p,v,t],[p,q,v],[t,p,v],[v,p,q]][i] as number[];
  return '#' + rgb.map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join('');
}
function hexToHsv(hex: string) {
  if (!hex || hex.length < 7) return { h: 0, s: 0, v: 1 };
  const r = parseInt(hex.slice(1,3),16)/255, g = parseInt(hex.slice(3,5),16)/255, b = parseInt(hex.slice(5,7),16)/255;
  const mx = Math.max(r,g,b), mn = Math.min(r,g,b), d = mx - mn;
  let h = 0;
  if (d) {
    if (mx===r) h = ((g-b)/d + (g<b?6:0))*60;
    else if (mx===g) h = ((b-r)/d + 2)*60;
    else h = ((r-g)/d + 4)*60;
  }
  return { h, s: mx===0?0:d/mx, v: mx };
}
function isHex(s: string) { return /^#[0-9A-Fa-f]{6}$/.test(s); }
function esc(s: string) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

/* ── HSV Canvas Picker ────────────────────────── */
function useHsvPicker(
  wrapId: string, canvasId: string, cursorId: string,
  hueBarId: string, hueThumbId: string, hexInputId: string, hexPreviewId: string,
  state: { h:number; s:number; v:number },
  onColor: (hex: string) => void
) {
  const dragSV = useRef(false), dragH = useRef(false);

  function drawCanvas() {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement | null;
    if (!canvas) return;
    const wrap = canvas.parentElement!;
    const w = wrap.getBoundingClientRect().width || 240;
    const h = Math.round(w * 0.6);
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext('2d')!;
    const gH = ctx.createLinearGradient(0,0,w,0);
    gH.addColorStop(0,'#fff'); gH.addColorStop(1,`hsl(${state.h},100%,50%)`);
    ctx.fillStyle = gH; ctx.fillRect(0,0,w,h);
    const gV = ctx.createLinearGradient(0,0,0,h);
    gV.addColorStop(0,'rgba(0,0,0,0)'); gV.addColorStop(1,'#000');
    ctx.fillStyle = gV; ctx.fillRect(0,0,w,h);
  }

  function apply() {
    const hex = hsvToHex(state.h, state.s, state.v);
    const cursor = document.getElementById(cursorId);
    const thumb  = document.getElementById(hueThumbId);
    const hexIn  = document.getElementById(hexInputId) as HTMLInputElement | null;
    const prev   = document.getElementById(hexPreviewId);
    if (cursor) { cursor.style.left = state.s*100+'%'; cursor.style.top = (1-state.v)*100+'%'; }
    if (thumb)  thumb.style.left = state.h/360*100+'%';
    if (hexIn)  hexIn.value = hex;
    if (prev)   prev.style.background = hex;
    onColor(hex);
  }

  useEffect(() => {
    const wrap   = document.getElementById(wrapId);
    const hueBar = document.getElementById(hueBarId);
    if (!wrap || !hueBar) return;

    function getSV(e: MouseEvent | TouchEvent) {
      const rc = wrap!.getBoundingClientRect();
      const cx = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
      const cy = 'touches' in e ? e.touches[0].clientY : (e as MouseEvent).clientY;
      return { s: Math.max(0,Math.min(1,(cx-rc.left)/rc.width)), v: 1-Math.max(0,Math.min(1,(cy-rc.top)/rc.height)) };
    }
    function getH(e: MouseEvent | TouchEvent) {
      const rc = hueBar!.getBoundingClientRect();
      const cx = 'touches' in e ? e.touches[0].clientX : (e as MouseEvent).clientX;
      return Math.max(0,Math.min(1,(cx-rc.left)/rc.width))*360;
    }

    const onMD = (e: MouseEvent) => { e.preventDefault(); dragSV.current=true; const sv=getSV(e); state.s=sv.s; state.v=sv.v; apply(); };
    const onHMD = (e: MouseEvent) => { e.preventDefault(); dragH.current=true; state.h=getH(e); drawCanvas(); apply(); };
    const onTD = (e: TouchEvent) => { e.preventDefault(); dragSV.current=true; const sv=getSV(e); state.s=sv.s; state.v=sv.v; apply(); };
    const onHTD = (e: TouchEvent) => { e.preventDefault(); dragH.current=true; state.h=getH(e); drawCanvas(); apply(); };
    const onMM = (e: MouseEvent) => { if(dragSV.current){const sv=getSV(e);state.s=sv.s;state.v=sv.v;apply();} if(dragH.current){state.h=getH(e);drawCanvas();apply();} };
    const onTM = (e: TouchEvent) => { if(dragSV.current){e.preventDefault();const sv=getSV(e);state.s=sv.s;state.v=sv.v;apply();} if(dragH.current){e.preventDefault();state.h=getH(e);drawCanvas();apply();} };
    const onUp = () => { dragSV.current=false; dragH.current=false; };

    wrap.addEventListener('mousedown', onMD);
    wrap.addEventListener('touchstart', onTD, {passive:false});
    hueBar.addEventListener('mousedown', onHMD);
    hueBar.addEventListener('touchstart', onHTD, {passive:false});
    document.addEventListener('mousemove', onMM);
    document.addEventListener('touchmove', onTM, {passive:false});
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchend', onUp);

    const hexEl = document.getElementById(hexInputId) as HTMLInputElement | null;
    const hexHandler = () => {
      let v = hexEl!.value.trim();
      if (!v.startsWith('#')) v = '#'+v;
      if (isHex(v)) { const h=hexToHsv(v); state.h=h.h; state.s=h.s; state.v=h.v; drawCanvas(); apply(); }
    };
    hexEl?.addEventListener('input', hexHandler);

    drawCanvas(); apply();

    return () => {
      wrap.removeEventListener('mousedown', onMD);
      wrap.removeEventListener('touchstart', onTD);
      hueBar.removeEventListener('mousedown', onHMD);
      hueBar.removeEventListener('touchstart', onHTD);
      document.removeEventListener('mousemove', onMM);
      document.removeEventListener('touchmove', onTM);
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('touchend', onUp);
      hexEl?.removeEventListener('input', hexHandler);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wrapId]);

  return { redraw: drawCanvas, apply };
}

/* ════════════════════════════════════════════════
   MAIN COMPONENT
════════════════════════════════════════════════ */
export default function IconLibrary({ iconList, iconW, iconH, categories, totalCount }: Props) {
  /* state */
  const [search, setSearch]               = useState('');
  const [styleFilter, setStyleFilter]     = useState('');
  const [catFilter, setCatFilter]         = useState('all');
  const [globalColor, setGlobalColor]     = useState('#c8d6e8');
  const [modalColor, setModalColorState]  = useState('#c8d6e8');
  const [modalOpen, setModalOpen]         = useState(false);
  const [currentIcon, setCurrentIcon]     = useState<IconItem | null>(null);
  const [exportSize, setExportSize]       = useState(512);
  const [bucket, setBucket]               = useState<Record<string,string>>({});
  const [sidebarOpen, setSidebarOpen]     = useState(false);
  const [cdnModalOpen, setCdnModalOpen]   = useState(false);
  const [activeCdnTab, setActiveCdnTab]   = useState('quickstart');
  const [styleDropOpen, setStyleDropOpen] = useState(false);
  const [colorPanelOpen, setColorPanelOpen] = useState(false);
  const [modalCdnOpen, setModalCdnOpen]   = useState(false);
  const [activeMiniTab, setActiveMiniTab] = useState('html');
  const [toasts, setToasts]              = useState<{id:number;msg:string;type:string}[]>([]);

  /* hsv state refs (mutable, used by picker) */
  const gHsv = useRef({ h:210, s:0.15, v:0.91 });
  const mHsv = useRef({ h:210, s:0.15, v:0.91 });
  let toastId = useRef(0);

  /* ── toast ── */
  const toast = useCallback((msg: string, type='success') => {
    const id = ++toastId.current;
    setToasts(t => [...t, {id, msg, type}]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 2400);
  }, []);

  /* ── load bucket from localStorage ── */
  useEffect(() => {
    try {
      const s = localStorage.getItem('iconlib_bucket');
      if (s) setBucket(JSON.parse(s));
    } catch {}
  }, []);
  function saveBucket(b: Record<string,string>) {
    setBucket(b);
    localStorage.setItem('iconlib_bucket', JSON.stringify(b));
  }

  /* ── global color picker ── */
  useHsvPicker(
    'globalHsvWrap','globalHsvCanvas','globalHsvCursor',
    'globalHueBar','globalHueThumb','globalHexInput','globalHexPreviewDot',
    gHsv.current,
    (hex) => {
      setGlobalColor(hex);
      document.documentElement.style.setProperty('--icon-color', hex);
      localStorage.setItem('iconlib_color', hex);
    }
  );

  /* ── modal color picker ── */
  useHsvPicker(
    'modalHsvWrap','modalHsvCanvas','modalHsvCursor',
    'modalHueBar','modalHueThumb','modalHexInput','modalHexPreviewDot',
    mHsv.current,
    (hex) => {
      setModalColorState(hex);
      const w = document.getElementById('modalIconWrap');
      if (w) { const s = w.querySelector('svg'); if (s) s.style.color = hex; }
    }
  );

  /* restore global color */
  useEffect(() => {
    const sc = localStorage.getItem('iconlib_color');
    if (sc && isHex(sc)) {
      setGlobalColor(sc);
      document.documentElement.style.setProperty('--icon-color', sc);
      const hsv = hexToHsv(sc);
      gHsv.current.h = hsv.h; gHsv.current.s = hsv.s; gHsv.current.v = hsv.v;
    }
  }, []);

  /* close dropdowns on outside click */
  useEffect(() => {
    function h(e: MouseEvent) {
      if (!(e.target as Element).closest('#styleFilterWrap')) setStyleDropOpen(false);
      if (!(e.target as Element).closest('#globalColorWrap'))  setColorPanelOpen(false);
    }
    document.addEventListener('click', h);
    return () => document.removeEventListener('click', h);
  }, []);

  /* Escape key */
  useEffect(() => {
    function h(e: KeyboardEvent) {
      if (e.key === 'Escape') { setModalOpen(false); setSidebarOpen(false); setCdnModalOpen(false); }
    }
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, []);

  /* ── filtering ── */
  const visible = iconList.filter(icon => {
    const n = icon.name.toLowerCase();
    const srchOk  = !search || n.includes(search.toLowerCase());
    const styleOk = !styleFilter || n.includes(styleFilter);
    const catKws  = catFilter !== 'all' ? (categories[catFilter]?.keywords ?? []) : [];
    const catOk   = catFilter === 'all' || catKws.some(k => n.includes(k));
    return srchOk && styleOk && catOk;
  });

  /* ── open icon modal ── */
  function openModal(icon: IconItem) {
    setCurrentIcon(icon);
    const hsv = hexToHsv(globalColor);
    mHsv.current.h = hsv.h; mHsv.current.s = hsv.s; mHsv.current.v = hsv.v;
    setModalColorState(globalColor);
    setModalCdnOpen(false);
    setActiveMiniTab('html');
    setModalOpen(true);
    document.body.style.overflow = 'hidden';
  }
  function closeModal() {
    setModalOpen(false);
    document.body.style.overflow = '';
    setCurrentIcon(null);
  }

  /* ── SVG string helpers ── */
  function getSvgStr(size?: number, color?: string): string {
    if (!currentIcon) return '';
    const s = size ?? exportSize;
    const c = color ?? modalColor;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 ${iconW} ${iconH}" style="color:${c};fill:currentColor">${currentIcon.body}</svg>`;
  }

  /* ── download ── */
  function downloadSVG() {
    if (!currentIcon) return;
    const blob = new Blob([getSvgStr()], { type: 'image/svg+xml' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = currentIcon.name+'.svg'; a.click();
    URL.revokeObjectURL(a.href); toast('SVG downloaded!');
  }

  function svgToPNG(size: number, cb: (c: HTMLCanvasElement) => void) {
    const canvas = document.getElementById('pngCanvas') as HTMLCanvasElement;
    canvas.width = size; canvas.height = size;
    const ctx = canvas.getContext('2d')!;
    const img = new Image();
    img.onload = () => { ctx.clearRect(0,0,size,size); ctx.drawImage(img,0,0,size,size); cb(canvas); URL.revokeObjectURL(img.src); };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(getSvgStr(size))));
  }

  function downloadPNG() {
    svgToPNG(exportSize, c => { const a=document.createElement('a'); a.href=c.toDataURL('image/png'); a.download=currentIcon!.name+'.png'; a.click(); toast('PNG downloaded!'); });
  }

  function copySVG() {
    navigator.clipboard.writeText(getSvgStr(24)).then(() => toast('SVG copied!', 'info'));
  }

  function copyPNG() {
    svgToPNG(exportSize, c => {
      c.toBlob(blob => {
        if (!blob) return;
        navigator.clipboard.write([new ClipboardItem({'image/png': blob})]).then(() => toast('PNG copied!','info')).catch(() => toast('Copy not supported','warn'));
      });
    });
  }

  /* ── bucket ── */
  function toggleFav(e: React.MouseEvent, icon: IconItem) {
    e.stopPropagation();
    const next = { ...bucket };
    if (next[icon.name]) { delete next[icon.name]; toast('Removed from bucket','warn'); }
    else { next[icon.name] = icon.body; toast('Added to bucket!'); }
    saveBucket(next);
  }

  /* ── mini CDN code ── */
  function miniCode(tab: string, name: string): string {
    const cdn = '/api/icon';
    if (tab === 'html')   return `<!-- 1. Add to <head> once -->\n<script src="/api/cdn" defer></script>\n\n<!-- 2. Use anywhere -->\n<i data-icon="${name}" data-size="24"></i>`;
    if (tab === 'react')  return `import MdIcon from './components/MdIcon';\n\n<MdIcon name="${name}" size={24} color="currentColor" />`;
    if (tab === 'vue')    return `<MdIcon name="${name}" :size="24" color="currentColor" />`;
    if (tab === 'svelte') return `<MdIcon name="${name}" size={24} color="currentColor" />`;
    if (tab === 'next')   return `import MdIcon from '@/components/MdIcon';\n\n// Fetches: ${cdn}?name=${name}\n<MdIcon name="${name}" size={24} />`;
    return '';
  }

  const CDN_TABS = ['quickstart','react','vue','svelte','next','nuxt','api'];
  const MINI_TABS = ['html','react','vue','svelte','next'];

  const STYLE_OPTIONS = [
    { value:'', label:'All Styles' },
    { value:'bold', label:'Bold' },
    { value:'duotone', label:'Duotone' },
    { value:'line-duotone', label:'Line Duotone' },
    { value:'linear', label:'Linear' },
    { value:'outline', label:'Outline' },
    { value:'broken', label:'Broken' },
  ];

  const bucketKeys = Object.keys(bucket);

  /* ── slider fill CSS ── */
  function sliderStyle(val: number, min=16, max=2048) {
    const pct = ((val-min)/(max-min)*100).toFixed(1)+'%';
    return { '--pct': pct } as React.CSSProperties;
  }

  /* ─────────────── RENDER ─────────────── */
  return (
    <div className="wrapper">

      {/* ── Navbar ── */}
      <nav>
        <a className="nav-brand" href="#">
          <div className="nav-logo">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <span className="nav-title">MD Icon Library</span>
        </a>
        <div className="nav-actions">
          <button className="cdn-nav-btn" onClick={() => setCdnModalOpen(true)}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            <span>Use CDN</span>
          </button>
          <button className="bucket-btn" onClick={() => { setSidebarOpen(true); document.body.style.overflow='hidden'; }}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>
            My Bucket
            <span className={`bucket-count${bucketKeys.length>0?' visible':''}`}>{bucketKeys.length}</span>
          </button>
        </div>
      </nav>

      {/* ── Category bar ── */}
      <div className="cat-bar-outer">
        <div className="cat-bar">
          {Object.entries(categories).map(([key, cat]) => (
            <button
              key={key}
              className={`cat-chip${catFilter===key?' active':''}`}
              onClick={() => setCatFilter(key)}
            >{cat.label}</button>
          ))}
        </div>
      </div>

      {/* ── Main ── */}
      <main>
        {/* Toolbar */}
        <div className="toolbar">
          {/* Search */}
          <div className="search-wrap">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              type="text"
              className="search-input"
              placeholder={`Search ${totalCount} icons...`}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {/* Style filter */}
          <div className="custom-select-wrap" id="styleFilterWrap">
            <div
              className={`custom-select-trigger${styleDropOpen?' open':''}`}
              onClick={e => { e.stopPropagation(); setStyleDropOpen(o => !o); }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              <span>{STYLE_OPTIONS.find(o=>o.value===styleFilter)?.label ?? 'All Styles'}</span>
              <svg className="arr-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <div className={`custom-select-dropdown${styleDropOpen?' open':''}`}>
              {STYLE_OPTIONS.map(o => (
                <div key={o.value} className={`custom-select-option${styleFilter===o.value?' selected':''}`}
                  onClick={() => { setStyleFilter(o.value); setStyleDropOpen(false); }}>
                  {o.label}
                </div>
              ))}
            </div>
          </div>

          {/* Color picker */}
          <div className="color-picker-wrap" id="globalColorWrap">
            <div className="color-trigger" onClick={e => { e.stopPropagation(); setColorPanelOpen(o => !o); }}>
              <div className="color-swatch-preview" id="globalColorPreview" style={{background: globalColor}}/>
              Color
            </div>
            <div className={`color-panel${colorPanelOpen?' open':''}`}>
              <div className="hsv-canvas-wrap" id="globalHsvWrap">
                <canvas className="hsv-canvas" id="globalHsvCanvas"/>
                <div className="hsv-cursor" id="globalHsvCursor"/>
              </div>
              <div className="hue-bar-wrap" id="globalHueBar">
                <div className="hue-thumb" id="globalHueThumb"/>
              </div>
              <div className="color-hex-row">
                <span className="color-hex-label">HEX</span>
                <input type="text" className="color-hex-input" id="globalHexInput" maxLength={7} placeholder="#c8d6e8"/>
                <div className="color-preview-dot" id="globalHexPreviewDot"/>
              </div>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="results-bar">
          <span className="results-count"><span>{visible.length}</span> icons</span>
        </div>

        {/* Icon grid */}
        <div className="icon-grid">
          {visible.length === 0 && (
            <div className="no-results">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <p>No icons found</p>
            </div>
          )}
          {visible.map(icon => (
            <div
              key={icon.name}
              className="icon-card"
              onClick={() => openModal(icon)}
            >
              <button
                className={`icon-card-fav${bucket[icon.name]?' active':''}`}
                title="Add to Bucket"
                onClick={e => toggleFav(e, icon)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
              </button>
              <div className="icon-card-svg">
                <svg xmlns="http://www.w3.org/2000/svg" width={iconW} height={iconH} viewBox={`0 0 ${iconW} ${iconH}`}
                  dangerouslySetInnerHTML={{__html: icon.body}}/>
              </div>
              <div className="icon-card-name">{icon.name}</div>
            </div>
          ))}
        </div>
      </main>

      {/* ── Icon Modal ── */}
      <div className={`modal-overlay${modalOpen?' open':''}`} onClick={e => { if(e.target===e.currentTarget) closeModal(); }}>
        <div className="modal">
          <div className="modal-header">
            <span className="modal-title">Icon Preview</span>
            <button className="modal-close" onClick={closeModal}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          {currentIcon && (
            <>
              <div className="modal-preview">
                <div className="modal-icon-wrap" id="modalIconWrap">
                  <svg xmlns="http://www.w3.org/2000/svg" width="66" height="66" viewBox={`0 0 ${iconW} ${iconH}`}
                    style={{color: modalColor, fill:'currentColor'}}
                    dangerouslySetInnerHTML={{__html: currentIcon.body}}/>
                </div>
                <div className="modal-icon-name">{currentIcon.name}</div>
              </div>
              <div className="modal-body">
                {/* Export size */}
                <div className="modal-section">
                  <div className="modal-section-label">Export Size</div>
                  <div className="size-row">
                    <div className="size-display">{exportSize}px</div>
                    <div className="size-slider-wrap">
                      <input type="range" className="size-slider" min={16} max={2048} step={8}
                        value={exportSize} style={sliderStyle(exportSize)}
                        onChange={e => setExportSize(Number(e.target.value))}/>
                    </div>
                  </div>
                </div>

                {/* Color */}
                <div className="modal-section">
                  <div className="modal-section-label">Icon Color</div>
                  <div className="modal-color-card">
                    <div className="hsv-canvas-wrap" id="modalHsvWrap">
                      <canvas className="hsv-canvas" id="modalHsvCanvas"/>
                      <div className="hsv-cursor" id="modalHsvCursor"/>
                    </div>
                    <div className="hue-bar-wrap" id="modalHueBar">
                      <div className="hue-thumb" id="modalHueThumb"/>
                    </div>
                    <div className="color-hex-row">
                      <span className="color-hex-label">HEX</span>
                      <input type="text" className="color-hex-input" id="modalHexInput" maxLength={7} placeholder="#c8d6e8"/>
                      <div className="color-preview-dot" id="modalHexPreviewDot"/>
                    </div>
                  </div>
                </div>

                {/* CDN usage inside modal */}
                <div className="modal-section">
                  <div className="modal-section-label">Use via CDN</div>
                  <div className="modal-cdn-section">
                    <div className="modal-cdn-header" onClick={() => setModalCdnOpen(o => !o)}>
                      <span className="modal-cdn-header-title">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                        CDN Usage Code
                      </span>
                      <svg className={`modal-cdn-chevron${modalCdnOpen?' open':''}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
                    </div>
                    <div className={`modal-cdn-body${modalCdnOpen?' open':''}`}>
                      <div className="mini-tabs">
                        {MINI_TABS.map(t => (
                          <button key={t} className={`mini-tab${activeMiniTab===t?' active':''}`}
                            onClick={() => setActiveMiniTab(t)}>{t}</button>
                        ))}
                      </div>
                      {MINI_TABS.map(t => (
                        <div key={t} className={`mini-code-panel${activeMiniTab===t?' active':''}`}>
                          <div className="mini-code-block">
                            <button className="mini-copy-btn" onClick={() => {
                              navigator.clipboard.writeText(miniCode(t, currentIcon.name)).then(() => toast('Code copied!','info'));
                            }}>Copy</button>
                            <pre><code>{miniCode(t, currentIcon.name)}</code></pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="modal-actions">
                  <button className="action-btn btn-dl-svg" onClick={downloadSVG}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download SVG
                  </button>
                  <button className="action-btn btn-dl-png" onClick={downloadPNG}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download PNG
                  </button>
                  <button className="action-btn btn-cp-svg" onClick={copySVG}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                    Copy SVG
                  </button>
                  <button className="action-btn btn-cp-png" onClick={copyPNG}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                    Copy PNG
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Bucket Sidebar ── */}
      <div className={`sidebar-overlay${sidebarOpen?' open':''}`} onClick={() => { setSidebarOpen(false); document.body.style.overflow=''; }}/>
      <div className={`sidebar${sidebarOpen?' open':''}`}>
        <div className="sidebar-header">
          <div className="sidebar-title-wrap">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>
            <span className="sidebar-title">My Bucket</span>
            <span className="sidebar-badge">{bucketKeys.length}</span>
          </div>
          <button className="sidebar-close" onClick={() => { setSidebarOpen(false); document.body.style.overflow=''; }}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div className="sidebar-body">
          {bucketKeys.length === 0 ? (
            <div className="sidebar-empty">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>
              <p>Bucket is empty.<br/>Tap the heart on any icon.</p>
            </div>
          ) : (
            <div className="bucket-list">
              {bucketKeys.map(name => (
                <div key={name} className="bucket-item" onClick={() => { openModal({name, body: bucket[name]}); setSidebarOpen(false); document.body.style.overflow=''; }}>
                  <div className="bucket-item-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox={`0 0 ${iconW} ${iconH}`}
                      style={{fill:'currentColor', color: globalColor}}
                      dangerouslySetInnerHTML={{__html: bucket[name]}}/>
                  </div>
                  <div className="bucket-item-name">{name}</div>
                  <button className="bucket-item-remove" onClick={e => { e.stopPropagation(); const n={...bucket}; delete n[name]; saveBucket(n); toast('Removed','warn'); }}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── CDN Docs Modal ── */}
      <div className={`cdn-modal-overlay${cdnModalOpen?' open':''}`} onClick={e => { if(e.target===e.currentTarget){ setCdnModalOpen(false); document.body.style.overflow=''; }}}>
        <div className="cdn-modal">
          <div className="cdn-modal-head">
            <div className="cdn-modal-title-group">
              <div className="cdn-modal-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              </div>
              <div>
                <div className="cdn-modal-title">CDN Integration Docs</div>
                <div className="cdn-modal-subtitle">Drop one &lt;script&gt; → icons render everywhere</div>
              </div>
            </div>
            <button className="cdn-modal-close" onClick={() => { setCdnModalOpen(false); document.body.style.overflow=''; }}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          {/* Hero */}
          <div className="cdn-url-hero">
            <div className="cdn-url-label">Add to &lt;head&gt; — done</div>
            <div className="cdn-url-row">
              <div className="cdn-url-text">&lt;script src="/api/cdn" defer&gt;&lt;/script&gt;</div>
              <button className="cdn-copy-btn" onClick={() => {
                navigator.clipboard.writeText('<script src="/api/cdn" defer></script>').then(() => toast('Script tag copied!','info'));
              }}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                Copy
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="cdn-tabs-wrap">
            {CDN_TABS.map(t => (
              <button key={t} className={`cdn-tab${activeCdnTab===t?' active':''}`}
                onClick={() => setActiveCdnTab(t)}>
                {t === 'quickstart' ? 'Quick Start' : t === 'api' ? 'API Ref' : t.charAt(0).toUpperCase()+t.slice(1)}
              </button>
            ))}
          </div>

          {/* Tab bodies */}
          <div className="cdn-modal-body">

            {/* Quick Start */}
            {activeCdnTab === 'quickstart' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Works like <strong>Font Awesome CDN</strong>. Add one script tag, then use <strong>data-icon=""</strong> anywhere.</span>
                </div>
                <div className="fw-badges"><span className="fw-badge html">HTML</span><span className="fw-badge cdn">Vanilla JS</span><span className="fw-badge next">WordPress</span></div>
                <div className="cdn-section">
                  <div className="cdn-section-label">Step 1 — Add to &lt;head&gt;</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">html</span>
                    <button className="cdn-code-copy" onClick={e => {
                      const pre = (e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!;
                      navigator.clipboard.writeText(pre.innerText).then(() => { (e.currentTarget as HTMLButtonElement).textContent='Copied!'; setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500); });
                    }}>Copy</button>
                    <pre><code>{`<head>\n  <script src="/api/cdn" defer></script>\n</head>`}</code></pre>
                  </div>
                </div>
                <div className="cdn-section">
                  <div className="cdn-section-label">Step 2 — Use icons anywhere</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">html</span>
                    <button className="cdn-code-copy" onClick={e => {
                      const pre = (e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!;
                      navigator.clipboard.writeText(pre.innerText).then(() => { (e.currentTarget as HTMLButtonElement).textContent='Copied!'; setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500); });
                    }}>Copy</button>
                    <pre><code>{`<!-- Basic -->\n<i data-icon="home-smile"></i>\n\n<!-- Custom size -->\n<i data-icon="arrow-right" data-size="32"></i>\n\n<!-- With color -->\n<i data-icon="heart" data-size="28" style="color:#f43f5e"></i>\n\n<!-- data-color attribute -->\n<i data-icon="star" data-size="24" data-color="#f59e0b"></i>`}</code></pre>
                  </div>
                </div>
              </div>
            )}

            {/* React */}
            {activeCdnTab === 'react' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Reusable <strong>&lt;MdIcon /&gt;</strong> — fetches each icon on-demand from <strong>/api/icon?name=NAME</strong>.</span>
                </div>
                <div className="fw-badges"><span className="fw-badge react">React 18+</span></div>
                <div className="cdn-section">
                  <div className="cdn-section-label">components/MdIcon.jsx</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">jsx</span>
                    <button className="cdn-code-copy" onClick={e => { const pre=(e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!; navigator.clipboard.writeText(pre.innerText).then(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copied!';setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500);}); }}>Copy</button>
                    <pre><code>{`import { useState, useEffect } from 'react';\n\nconst cache = {};\n\nexport default function MdIcon({ name, size = 24, color = 'currentColor', className = '' }) {\n  const [svg, setSvg] = useState('');\n\n  useEffect(() => {\n    if (!name) return;\n    if (cache[name]) { setSvg(cache[name]); return; }\n    fetch(\`/api/icon?name=\${encodeURIComponent(name)}&size=\${size}\`)\n      .then(r => r.text())\n      .then(s => { cache[name] = s; setSvg(s); });\n  }, [name, size]);\n\n  if (!svg) return null;\n  return (\n    <span className={className} style={{ color, display:'inline-flex', alignItems:'center' }}\n      dangerouslySetInnerHTML={{ __html: svg }} />\n  );\n}`}</code></pre>
                  </div>
                </div>
                <div className="cdn-section">
                  <div className="cdn-section-label">Usage</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">jsx</span>
                    <button className="cdn-code-copy" onClick={e => { const pre=(e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!; navigator.clipboard.writeText(pre.innerText).then(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copied!';setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500);}); }}>Copy</button>
                    <pre><code>{`import MdIcon from './components/MdIcon';\n\n<MdIcon name="home-smile" size={32} color="#4db8ff" />\n<MdIcon name="arrow-right" size={20} />`}</code></pre>
                  </div>
                </div>
              </div>
            )}

            {/* Vue */}
            {activeCdnTab === 'vue' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Vue 3 Composition API — fetches SVG from <strong>/api/icon</strong>.</span>
                </div>
                <div className="fw-badges"><span className="fw-badge vue">Vue 3</span></div>
                <div className="cdn-section">
                  <div className="cdn-section-label">components/MdIcon.vue</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">vue</span>
                    <button className="cdn-code-copy" onClick={e => { const pre=(e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!; navigator.clipboard.writeText(pre.innerText).then(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copied!';setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500);}); }}>Copy</button>
                    <pre><code>{`<script setup>\nimport { ref, watch, onMounted } from 'vue';\nconst props = defineProps({ name: String, size: { default: 24 }, color: { default: 'currentColor' } });\nconst cache = {};\nconst svg = ref('');\nasync function load() {\n  if (!props.name) return;\n  if (cache[props.name]) { svg.value = cache[props.name]; return; }\n  const res = await fetch(\`/api/icon?name=\${props.name}&size=\${props.size}\`);\n  svg.value = cache[props.name] = await res.text();\n}\nonMounted(load);\nwatch(() => props.name, load);\n</script>\n\n<template>\n  <span :style="\`color:\${color};display:inline-flex\`" v-html="svg" />\n</template>`}</code></pre>
                  </div>
                </div>
              </div>
            )}

            {/* Svelte */}
            {activeCdnTab === 'svelte' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Reactive Svelte component — fetches on demand.</span>
                </div>
                <div className="fw-badges"><span className="fw-badge svelte">Svelte 4+</span><span className="fw-badge svelte">SvelteKit</span></div>
                <div className="cdn-section">
                  <div className="cdn-section-label">lib/MdIcon.svelte</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">svelte</span>
                    <button className="cdn-code-copy" onClick={e => { const pre=(e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!; navigator.clipboard.writeText(pre.innerText).then(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copied!';setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500);}); }}>Copy</button>
                    <pre><code>{`<script>\n  export let name = '', size = 24, color = 'currentColor';\n  const cache = {};\n  let svg = '';\n  $: name, load();\n  async function load() {\n    if (!name) return;\n    if (cache[name]) { svg = cache[name]; return; }\n    svg = cache[name] = await fetch(\`/api/icon?name=\${name}&size=\${size}\`).then(r => r.text());\n  }\n</script>\n{#if svg}\n  <span style="color:{color};display:inline-flex">{@html svg}</span>\n{/if}`}</code></pre>
                  </div>
                </div>
              </div>
            )}

            {/* Next.js */}
            {activeCdnTab === 'next' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Use <strong>'use client'</strong> — TypeScript-ready.</span>
                </div>
                <div className="fw-badges"><span className="fw-badge next">Next.js 14+</span><span className="fw-badge react">App Router</span></div>
                <div className="cdn-section">
                  <div className="cdn-section-label">components/MdIcon.tsx</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">tsx</span>
                    <button className="cdn-code-copy" onClick={e => { const pre=(e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!; navigator.clipboard.writeText(pre.innerText).then(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copied!';setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500);}); }}>Copy</button>
                    <pre><code>{`'use client';\nimport { useState, useEffect } from 'react';\nconst cache: Record<string,string> = {};\ninterface Props { name: string; size?: number; color?: string; className?: string; }\nexport default function MdIcon({ name, size=24, color='currentColor', className='' }: Props) {\n  const [svg, setSvg] = useState('');\n  useEffect(() => {\n    if (!name) return;\n    if (cache[name]) { setSvg(cache[name]); return; }\n    fetch(\`/api/icon?name=\${encodeURIComponent(name)}&size=\${size}\`)\n      .then(r => r.text()).then(s => { cache[name]=s; setSvg(s); });\n  }, [name, size]);\n  if (!svg) return null;\n  return <span className={className} style={{ color, display:'inline-flex', alignItems:'center' }}\n    dangerouslySetInnerHTML={{ __html: svg }} />;\n}`}</code></pre>
                  </div>
                </div>
              </div>
            )}

            {/* Nuxt */}
            {activeCdnTab === 'nuxt' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Auto-imported composable for Nuxt 3.</span>
                </div>
                <div className="fw-badges"><span className="fw-badge nuxt">Nuxt 3</span><span className="fw-badge vue">Vue 3</span></div>
                <div className="cdn-section">
                  <div className="cdn-section-label">composables/useMdIcon.ts</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">ts</span>
                    <button className="cdn-code-copy" onClick={e => { const pre=(e.currentTarget as HTMLElement).closest('.cdn-code-block')!.querySelector('pre')!; navigator.clipboard.writeText(pre.innerText).then(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copied!';setTimeout(()=>{(e.currentTarget as HTMLButtonElement).textContent='Copy';},1500);}); }}>Copy</button>
                    <pre><code>{`const cache: Record<string,string> = {};\nexport function useMdIcon(name: string, size = 24) {\n  const svg = ref('');\n  watchEffect(async () => {\n    if (!name) return;\n    if (cache[name]) { svg.value = cache[name]; return; }\n    svg.value = cache[name] = await fetch(\`/api/icon?name=\${name}&size=\${size}\`).then(r => r.text());\n  });\n  return svg;\n}`}</code></pre>
                  </div>
                </div>
              </div>
            )}

            {/* API Ref */}
            {activeCdnTab === 'api' && (
              <div>
                <div className="cdn-note">
                  <span className="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                  <span className="cdn-note-text">Each icon is served individually — <strong>bulk JSON is never exposed</strong>.</span>
                </div>
                <div className="cdn-section">
                  <div className="cdn-section-label">Endpoints</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">url</span>
                    <pre><code>{`GET /api/cdn\n→ JS loader script (put in <head> defer)\n\nGET /api/icon?name={icon-name}&size=24&color=%234db8ff\n→ SVG image  (Content-Type: image/svg+xml)\n→ Cached 24h`}</code></pre>
                  </div>
                </div>
                <div className="cdn-section">
                  <div className="cdn-section-label">HTML attributes</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">html</span>
                    <pre><code>{`<i\n  data-icon="icon-name"   <!-- required -->\n  data-size="24"          <!-- optional, px -->\n  data-color="#4db8ff"    <!-- optional, hex -->\n  style="color:#4db8ff"  <!-- CSS color also works -->\n></i>`}</code></pre>
                  </div>
                </div>
                <div className="cdn-section">
                  <div className="cdn-section-label">Security</div>
                  <div className="cdn-code-block">
                    <span className="cdn-code-lang">text</span>
                    <pre><code>{`✓  Per-icon serving   — no bulk JSON dump\n✓  Rate limiting      — 300 req/min per IP\n✓  Name sanitisation  — only [a-z0-9-] accepted\n✓  SVG output only    — not raw JSON\n✓  Cache headers      — 24h browser cache`}</code></pre>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      {/* ── Toasts ── */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className="toast">
            <div className={`toast-dot${t.type==='warn'?' warn':t.type==='info'?' info':''}`}/>
            {esc(t.msg)}
          </div>
        ))}
      </div>

      <canvas id="pngCanvas" style={{display:'none'}}/>
    </div>
  );
}
