import { NextRequest, NextResponse } from 'next/server';

const RATE_MAP = new Map<string, { count: number; ts: number }>();
const RATE_LIMIT = 300;

function rateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = RATE_MAP.get(ip);
  if (!entry || now - entry.ts > 60_000) {
    RATE_MAP.set(ip, { count: 1, ts: now });
    return true;
  }
  entry.count++;
  return entry.count <= RATE_LIMIT;
}

export async function GET(req: NextRequest) {
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0].trim() ?? '0.0.0.0';

  if (!rateLimit(ip)) {
    return new NextResponse('Rate limit exceeded', { status: 429 });
  }

  const host    = req.headers.get('host') ?? 'icons.mdjhs.com';
  const proto   = req.headers.get('x-forwarded-proto') ?? 'https';
  const base    = `${proto}://${host}`;
  const iconApi = `${base}/api/icon`;

  const script = `
/**
 * MD Icon CDN Loader
 * Usage: <script src="${base}/api/cdn" defer><\/script>
 *        <i data-icon="home-smile" data-size="24" style="color:#4db8ff"><\/i>
 */
(function () {
  'use strict';
  var BASE = '${iconApi}';
  var cache = {};

  function fetchIcon(name, cb) {
    if (cache[name]) { cb(cache[name]); return; }
    fetch(BASE + '?name=' + encodeURIComponent(name))
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (svg) { if (svg) { cache[name] = svg; cb(svg); } })
      .catch(function () {});
  }

  function renderEl(el) {
    if (el._mdDone) return;
    el._mdDone = true;
    var name  = el.getAttribute('data-icon');
    var size  = el.getAttribute('data-size')  || '24';
    var color = el.getAttribute('data-color') || '';
    if (!name) return;
    fetchIcon(name, function (svg) {
      var out = svg
        .replace(/width="[^"]*"/, 'width="' + size + '"')
        .replace(/height="[^"]*"/, 'height="' + size + '"');
      if (color) out = out.replace(/fill="[^"]*"/, 'fill="' + color + '"');
      var wrap = document.createElement('span');
      wrap.className    = el.className;
      wrap.style.cssText = el.style.cssText;
      wrap.style.display = wrap.style.display || 'inline-flex';
      wrap.style.alignItems = 'center';
      wrap.innerHTML = out;
      if (el.parentNode) el.parentNode.replaceChild(wrap, el);
    });
  }

  function renderAll() {
    document.querySelectorAll('[data-icon]').forEach(renderEl);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderAll);
  } else {
    renderAll();
  }

  new MutationObserver(function (muts) {
    muts.forEach(function (m) {
      m.addedNodes.forEach(function (n) {
        if (n.nodeType !== 1) return;
        if (n.hasAttribute && n.hasAttribute('data-icon')) renderEl(n);
        if (n.querySelectorAll) n.querySelectorAll('[data-icon]').forEach(renderEl);
      });
    });
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
`.trim();

  return new NextResponse(script, {
    headers: {
      'Content-Type': 'application/javascript; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
