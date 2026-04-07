import os
import json
import time
import hashlib
import tempfile
import re
from flask import Flask, request, jsonify, make_response, render_template_string

app = Flask(__name__)

# ── Configuration & Data ───────────────────────────────────────
ICON_FILE = 'icons.json'
RATE_LIMIT_PER_MINUTE = 300
ALLOWED_ORIGINS = [
    'https://icons.mdjhs.com',
    'https://icons.pro.bd',
    'https://icons.microstock.store',
    'http://localhost',
    'http://127.0.0.1',
]

iconsData = {}
allIcons = {}
globalWidth = 24
globalHeight = 24

# Load icons.json at startup
if os.path.exists(ICON_FILE):
    try:
        with open(ICON_FILE, 'r', encoding='utf-8') as f:
            iconsData = json.load(f)
        allIcons = iconsData.get('icons', {})
        globalWidth = iconsData.get('width', 24)
        globalHeight = iconsData.get('height', 24)
    except Exception as e:
        print("Error loading icons.json:", e)

CATEGORIES = {
    'all':             {'label': 'All Icons',       'keywords': []},
    'arrows':          {'label': 'Arrows',          'keywords': ['arrow','chevron','caret','direction','sort','transfer','alt-arrow','double-alt','round-arrow','square-arrow']},
    'arrows-action':   {'label': 'Arrows Action',   'keywords': ['refresh','restart','reload','rotate','undo','redo','sync','reverse']},
    'messages':        {'label': 'Messages',        'keywords': ['chat','message','dialog','inbox','letter','mail','plain','paperclip','unread','forward','reply']},
    'map':             {'label': 'Map',             'keywords': ['map','compass','location','gps','navigation','route','pin','place','people-nearby']},
    'video':           {'label': 'Video',           'keywords': ['video','camera','film','movie','play','pause','record','stream','reel','clapperboard']},
    'money':           {'label': 'Money',           'keywords': ['money','wallet','coin','currency','dollar','payment','bank','finance','cash','card','price','pay']},
    'devices':         {'label': 'Devices',         'keywords': ['phone','mobile','laptop','computer','tablet','device','screen','monitor','keyboard','mouse','printer','server']},
    'weather':         {'label': 'Weather',         'keywords': ['weather','sun','cloud','rain','snow','wind','storm','fog','temperature','lightning','moon','sky']},
    'files':           {'label': 'Files',           'keywords': ['file','document','pdf','doc','zip','download','upload','attachment','clip','page']},
    'astronomy':       {'label': 'Astronomy',       'keywords': ['star','planet','moon','space','galaxy','orbit','telescope','asteroid','comet','solar','universe']},
    'folders':         {'label': 'Folders',         'keywords': ['folder','directory','archive','library','collection','bookmark']},
    'faces':           {'label': 'Faces',           'keywords': ['face','emoji','smile','sad','happy','emotion','mood','avatar','head','expression']},
    'search':          {'label': 'Search',          'keywords': ['search','find','magnify','explore','scan','filter','zoom']},
    'sports':          {'label': 'Sports',          'keywords': ['sport','ball','football','basketball','tennis','soccer','gym','fitness','run','swim','medal','trophy','game']},
    'time':            {'label': 'Time',            'keywords': ['time','clock','alarm','timer','calendar','date','schedule','watch','hour','minute']},
    'list-ui':         {'label': 'List UI',         'keywords': ['list','grid','menu','table','row','column','layout','sidebar','panel','widget','ui','view','dashboard']},
    'call':            {'label': 'Call',            'keywords': ['call','phone','dial','contact','voip','receiver','headset','handset']},
    'medicine':        {'label': 'Medicine',        'keywords': ['medicine','health','hospital','pill','drug','doctor','medical','heart','pulse','ambulance','stethoscope','virus','vaccine']},
    'home':            {'label': 'Home & IT',       'keywords': ['home','house','door','window','sofa','room','kitchen','wifi','router','cable','signal','network','server','cloud']},
    'settings':        {'label': 'Settings',        'keywords': ['setting','config','gear','wrench','tool','option','adjust','preference','control','switch','toggle']},
    'text-formatting': {'label': 'Text Formatting', 'keywords': ['text','font','bold','italic','underline','align','paragraph','heading','list','quote','link','code','format','type']},
    'business':        {'label': 'Business',        'keywords': ['business','office','briefcase','work','project','chart','graph','analytics','report','meeting','presentation','target']},
    'shopping':        {'label': 'Shopping',        'keywords': ['shop','cart','bag','store','buy','product','order','checkout','coupon','gift','sale','discount']},
    'nature':          {'label': 'Nature',          'keywords': ['nature','tree','leaf','flower','plant','animal','bird','ocean','mountain','river','eco','green']},
    'school':          {'label': 'School',          'keywords': ['school','book','education','learn','study','pen','pencil','notebook','class','teacher','student','graduation','library']},
    'tools':           {'label': 'Tools',           'keywords': ['tool','hammer','screwdriver','drill','saw','wrench','fix','repair','build','construct']},
    'food':            {'label': 'Food',            'keywords': ['food','drink','eat','restaurant','coffee','tea','cake','fruit','vegetable','cook','kitchen','recipe','meal']},
    'like':            {'label': 'Like',            'keywords': ['like','love','heart','favorite','star','rating','thumbs','reaction','vote','bookmark','save']},
    'notes':           {'label': 'Notes',           'keywords': ['note','memo','sticky','pad','write','edit','annotation','comment','label','tag']},
    'notifications':   {'label': 'Notifications',   'keywords': ['notification','bell','alert','badge','reminder','announce','warning','info']},
    'security':        {'label': 'Security',        'keywords': ['security','lock','shield','key','password','private','protect','safe','virus','firewall','encrypt','auth']},
    'users':           {'label': 'Users',           'keywords': ['user','people','person','profile','account','team','group','member','contact','friend']},
    'building':        {'label': 'Building',        'keywords': ['building','office','bank','hotel','hospital','school','city','house','store','factory','skyscraper']},
    'hands-parts':     {'label': 'Hands & Parts',   'keywords': ['hand','finger','thumb','gesture','body','arm','eye','ear','mouth','touch','point','wave']},
}

catJS = {k: v['keywords'] for k, v in CATEGORIES.items()}
catJSEncoded = json.dumps(catJS)

# ── Rate Limiting ──────────────────────────────────────────────
def rate_limit_check(ip, limit):
    temp_dir = os.path.join(tempfile.gettempdir(), 'mdicons_rl')
    os.makedirs(temp_dir, exist_ok=True)
    ip_hash = hashlib.md5(ip.encode('utf-8')).hexdigest()
    file_path = os.path.join(temp_dir, f"{ip_hash}.json")
    now = int(time.time())
    data = {'minute': now, 'count': 0}
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                d = json.load(f)
            if now - d['minute'] < 60:
                data = d
        except:
            pass
            
    data['count'] += 1
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return data['count'] <= limit

def origin_allowed(origin, allowed):
    if not origin:
        return True
    for a in allowed:
        if origin.startswith(a):
            return True
    return False

def _build_cors_preflight_response(origin):
    resp = make_response()
    resp.status_code = 204
    resp.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

# ── JS Scripts ─────────────────────────────────────────────────
def get_v1_cdn_script(fetch_url):
    return f"""(function(){{
    const fUrl = "{fetch_url}";
    const cKey = "iconLib_public_cache";
    let cache = JSON.parse(localStorage.getItem(cKey) || "{{}}");

    function renderIcon(el, name) {{
        if(cache[name]) {{
            const w = cache.width || 24;
            const h = cache.height || 24;
            el.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'" fill="currentColor" style="display:inline-block; vertical-align:middle;">'+cache[name]+'</svg>';
            el.removeAttribute('data-icon');
            el.setAttribute('data-icon-rendered', name);
            return true;
        }}
        return false;
    }}

    let isFetching = false;
    let pending = [];

    function scanAndRender() {{
        const els = document.querySelectorAll('i[data-icon]');
        if(els.length === 0) return;

        let needsFetch = false;
        els.forEach(el => {{
            const n = el.getAttribute('data-icon');
            if(!renderIcon(el, n)) {{
                if(!pending.includes(n)) pending.push(n);
                needsFetch = true;
            }}
        }});

        if(needsFetch && !isFetching && pending.length > 0) {{
            isFetching = true;
            const toFetch = [...pending];
            fetch(fUrl, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ icons: toFetch }})
            }}).then(r => r.json()).then(d => {{
                let cUpdated = false;
                cache.width = d.width || 24;
                cache.height = d.height || 24;
                toFetch.forEach(n => {{
                    if(d[n]) {{ cache[n] = d[n]; cUpdated = true; }}
                    pending = pending.filter(p => p !== n);
                }});
                if(cUpdated) localStorage.setItem(cKey, JSON.stringify(cache));

                document.querySelectorAll('i[data-icon]').forEach(el => {{
                    renderIcon(el, el.getAttribute('data-icon'));
                }});
                isFetching = false;
                if(pending.length > 0) scanAndRender(); 
            }}).catch(() => {{ isFetching = false; }});
        }}
    }}

    scanAndRender();
    if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scanAndRender);
    const obs = new MutationObserver(m => {{
        let shouldScan = false;
        for(let i=0; i<m.length; i++) {{
            if(m[i].addedNodes.length > 0) {{ shouldScan = true; break; }}
        }}
        if(shouldScan) scanAndRender();
    }});
    if(document.documentElement) obs.observe(document.documentElement, {{ childList: true, subtree: true }});
}})();"""


def get_v2_cdn_script(cdn_base, host, total_icons):
    return f"""/**
 * MD Icon CDN Loader v2
 * Auto-renders [data-icon] elements on page load + MutationObserver
 *
 * Usage:
 * <script src="{cdn_base}" defer></script>
 * <i data-icon="home-smile" data-size="24" style="color:#4db8ff"></i>
 *
 * Attributes:
 * data-icon   — icon name (required)
 * data-size   — pixel size (default: 24)
 * data-color  — fill color (default: currentColor / inherits CSS color)
 *
 * CDN: {host}
 * Icons available: {total_icons}
 */
(function () {{
  'use strict';

  var BASE = '{cdn_base}';
  var cache = {{}};

  function fetchIcon(name, cb) {{
    if (cache[name]) {{ cb(cache[name]); return; }}
    fetch(BASE + '?icon=' + encodeURIComponent(name))
      .then(function (r) {{
        if (!r.ok) return null;
        return r.text();
      }})
      .then(function (svg) {{
        if (svg) {{ cache[name] = svg; cb(svg); }}
      }})
      .catch(function () {{}});
  }}

  function renderEl(el) {{
    if (el._mdRendered) return;
    el._mdRendered = true;

    var name  = el.getAttribute('data-icon');
    var size  = el.getAttribute('data-size')  || '24';
    var color = el.getAttribute('data-color') || '';
    if (!name) return;

    fetchIcon(name, function (svg) {{
      var out = svg
        .replace(/width="[^"]*"/, 'width="' + size + '"')
        .replace(/height="[^"]*"/, 'height="' + size + '"');

      if (color) {{
        out = out.replace(/fill="[^"]*"/, 'fill="' + color + '"');
      }}

      var wrap = document.createElement('span');
      wrap.className   = el.className;
      wrap.style.cssText = el.style.cssText;
      wrap.style.display = wrap.style.display || 'inline-flex';
      wrap.style.alignItems = 'center';
      wrap.innerHTML   = out;
      el.parentNode.replaceChild(wrap, el);
    }});
  }}

  function renderAll() {{
    document.querySelectorAll('[data-icon]').forEach(renderEl);
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', renderAll);
  }} else {{
    renderAll();
  }}

  var observer = new MutationObserver(function (mutations) {{
    mutations.forEach(function (m) {{
      m.addedNodes.forEach(function (node) {{
        if (node.nodeType !== 1) return;
        if (node.hasAttribute('data-icon')) renderEl(node);
        node.querySelectorAll && node.querySelectorAll('[data-icon]').forEach(renderEl);
      }});
    }});
  }});
  observer.observe(document.documentElement, {{ childList: true, subtree: true }});
}})();"""


# ── Routes ─────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def index():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response(request.headers.get('Origin', ''))

    action = request.args.get('action')
    cdn_flag = request.args.get('cdn')

    # Public CDN Fetch Endpoint
    if action == 'fetch':
        data = request.get_json(silent=True) or {}
        requested_icons = data.get('icons', [])
        response_data = {'width': globalWidth, 'height': globalHeight}
        for icon in requested_icons:
            if icon in allIcons:
                response_data[icon] = allIcons[icon].get('body', '')
        resp = jsonify(response_data)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # Public CDN Script Delivery
    if cdn_flag == 'true':
        fetch_url = request.url_root.rstrip('/') + request.path + '?cdn=true&action=fetch'
        js_payload = get_v1_cdn_script(fetch_url)
        resp = make_response(js_payload)
        resp.headers['Content-Type'] = 'application/javascript'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # Render Main Website
    siteTitle = "Premium Icon Library"
    baseCdnUrl = request.url_root.rstrip('/') + '/cdn.php'

    return render_template_string(HTML_TEMPLATE,
        siteTitle=siteTitle,
        globalWidth=globalWidth,
        globalHeight=globalHeight,
        allIcons=allIcons,
        CATEGORIES=CATEGORIES,
        catJSEncoded=catJSEncoded,
        baseCdnUrl=baseCdnUrl
    )


@app.route('/cdn.php', methods=['GET', 'OPTIONS'])
def cdn_endpoint():
    origin = request.headers.get('Origin', '')
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response(origin)

    if origin and not origin_allowed(origin, ALLOWED_ORIGINS):
        resp = jsonify({'error': 'Origin not allowed'})
        resp.status_code = 403
        return resp

    requested_icon = request.args.get('icon', '').strip()

    # Route A: Single Icon SVG
    if requested_icon:
        client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr or '0.0.0.0'
        if not rate_limit_check(client_ip, RATE_LIMIT_PER_MINUTE):
            resp = jsonify({'error': 'Rate limit exceeded. Slow down.'})
            resp.status_code = 429
            return resp

        requested_icon = re.sub(r'[^a-z0-9\-]', '', requested_icon.lower())

        if requested_icon not in allIcons:
            resp = jsonify({'error': f'Icon not found: {requested_icon}'})
            resp.status_code = 404
            return resp

        body = allIcons[requested_icon].get('body', '')
        color = request.args.get('color', 'currentColor')
        color = re.sub(r'[^a-fA-F0-9#]', '', color) if color != 'currentColor' else color
        size = request.args.get('size', globalWidth)
        try:
            size = max(8, min(2048, int(size)))
        except:
            size = globalWidth

        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {globalWidth} {globalHeight}" fill="{color}">{body}</svg>'

        resp = make_response(svg)
        resp.headers['Content-Type'] = 'image/svg+xml'
        resp.headers['Cache-Control'] = 'public, max-age=86400, immutable'
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        if origin:
            resp.headers['Access-Control-Allow-Origin'] = origin
            resp.headers['Vary'] = 'Origin'
        else:
            resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # Route B: CDN Loader Script v2
    host = request.url_root.rstrip('/')
    cdn_base = f"{host}/cdn.php"
    total_icons = len(allIcons)

    js_script = get_v2_cdn_script(cdn_base, host, total_icons)
    resp = make_response(js_script)
    resp.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    resp.headers['Cache-Control'] = 'public, max-age=3600'
    resp.headers['X-CDN-Icons'] = str(total_icons)
    if origin:
        resp.headers['Access-Control-Allow-Origin'] = origin
        resp.headers['Vary'] = 'Origin'
    else:
        resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


# ── HTML Template (Combined Index + Admin features) ────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ siteTitle }}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
    --icon-color: #c8d6e8;
    --bg-primary: #111318;
    --bg-secondary: #181c24;
    --bg-glass: rgba(255,255,255,0.05);
    --bg-glass-hover: rgba(255,255,255,0.09);
    --border-glass: rgba(255,255,255,0.09);
    --border-hover: rgba(99,196,255,0.45);
    --accent: #4db8ff;
    --accent-2: #7c6fff;
    --accent-light: #80cfff;
    --text-primary: #e8edf5;
    --text-secondary: #8fa0b8;
    --text-muted: #4a5568;
    --navbar-h: 62px;
    --cat-bar-h: 44px;
    --radius-card: 14px;
    --radius-btn: 9px;
    --transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: 'Plus Jakarta Sans', sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; overflow-x: hidden; }
body::before {
    content: ''; position: fixed; inset: 0;
    background: radial-gradient(ellipse 70% 45% at 15% 0%, rgba(77,184,255,0.07) 0%, transparent 55%),
                radial-gradient(ellipse 55% 40% at 85% 100%, rgba(124,111,255,0.06) 0%, transparent 55%);
    pointer-events: none; z-index: 0;
}
.wrapper { position: relative; z-index: 1; }

nav {
    position: fixed; top: 0; left: 0; right: 0; height: var(--navbar-h);
    background: rgba(17,19,24,0.85); backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border-bottom: 1px solid var(--border-glass);
    display: flex; align-items: center; padding: 0 1.5rem;
    justify-content: space-between; z-index: 1000;
    box-shadow: 0 2px 24px rgba(0,0,0,0.35);
}
.nav-brand { display: flex; align-items: center; gap: 0.65rem; text-decoration: none; }
.nav-logo { width: 34px; height: 34px; background: linear-gradient(135deg,#4db8ff,#7c6fff); border-radius: 9px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 16px rgba(77,184,255,0.35); flex-shrink: 0; }
.nav-logo svg { color: #fff; width: 18px; height: 18px; }
.nav-title { font-size: 0.98rem; font-weight: 700; background: linear-gradient(135deg,#e8edf5 0%,#8fa0b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: -0.02em; }
.nav-actions { display: flex; align-items: center; gap: 0.75rem; }
.bucket-btn { display: flex; align-items: center; gap: 0.45rem; padding: 0.45rem 1rem; background: rgba(77,184,255,0.12); border: 1px solid rgba(77,184,255,0.28); border-radius: 9999px; color: var(--accent-light); font-family: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: var(--transition); }
.bucket-btn:hover { background: rgba(77,184,255,0.22); border-color: rgba(77,184,255,0.5); transform: translateY(-1px); }
.bucket-btn svg { width: 15px; height: 15px; }
.bucket-count { background: linear-gradient(135deg,#4db8ff,#7c6fff); color: #fff; border-radius: 9999px; font-size: 0.7rem; font-weight: 700; min-width: 17px; height: 17px; display: none; align-items: center; justify-content: center; padding: 0 4px; }
.bucket-count.visible { display: flex; }

/* ── CDN Button in Nav ── */
.cdn-nav-btn {
    display: flex; align-items: center; gap: 0.45rem;
    padding: 0.45rem 1rem;
    background: linear-gradient(135deg, rgba(124,111,255,0.18), rgba(77,184,255,0.12));
    border: 1px solid rgba(124,111,255,0.35);
    border-radius: 9999px;
    color: #b8b0ff;
    font-family: inherit; font-size: 0.82rem; font-weight: 600;
    cursor: pointer; transition: var(--transition);
    white-space: nowrap;
}
.cdn-nav-btn:hover {
    background: linear-gradient(135deg, rgba(124,111,255,0.3), rgba(77,184,255,0.2));
    border-color: rgba(124,111,255,0.6);
    transform: translateY(-1px);
}
.cdn-nav-btn svg { width: 14px; height: 14px; flex-shrink: 0; }
.cdn-nav-btn .mobile-text { display: none; } /* Added based on prompt logic */

.cat-bar-outer { position: fixed; top: var(--navbar-h); left: 0; right: 0; height: var(--cat-bar-h); z-index: 900; background: rgba(17,19,24,0.9); backdrop-filter: blur(16px); border-bottom: 1px solid var(--border-glass); display: flex; align-items: center; padding: 0 1.5rem; overflow: hidden; }
.cat-bar { display: flex; gap: 0.35rem; overflow-x: auto; flex: 1; scrollbar-width: none; padding: 0.2rem 0; -webkit-overflow-scrolling: touch; }
.cat-bar::-webkit-scrollbar { display: none; }
.cat-chip { flex-shrink: 0; padding: 0.3rem 0.85rem; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: 9999px; font-family: inherit; font-size: 0.77rem; font-weight: 600; color: var(--text-secondary); cursor: pointer; transition: var(--transition); white-space: nowrap; }
.cat-chip:hover { background: var(--bg-glass-hover); color: var(--text-primary); }
.cat-chip.active { background: linear-gradient(135deg,rgba(77,184,255,0.22),rgba(124,111,255,0.18)); border-color: rgba(77,184,255,0.45); color: var(--accent-light); }

main { padding-top: calc(var(--navbar-h) + var(--cat-bar-h) + 1.25rem); padding-bottom: 4rem; padding-left: 1.5rem; padding-right: 1.5rem; max-width: 1400px; margin: 0 auto; }

/* Documentation Section */
.docs-section { background: rgba(17,19,24,0.6); border: 1px solid var(--border-glass); border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; position: relative; overflow: hidden; }
.docs-section::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background: linear-gradient(to bottom,#4db8ff,#7c6fff); }
.docs-title { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }
.docs-text { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 1rem; max-width: 800px; }
.docs-code { background: #0f1115; border: 1px solid var(--border-glass); padding: 0.85rem 1rem; border-radius: 8px; font-family: monospace; font-size: 0.85rem; color: #a5b4fc; display: flex; justify-content: space-between; align-items: center; }
.copy-docs-btn { background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-secondary); padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; font-weight: 600; transition: var(--transition); }
.copy-docs-btn:hover { background: var(--bg-glass-hover); color: var(--text-primary); }

.toolbar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.search-wrap { flex: 1; min-width: 200px; position: relative; }
.search-wrap svg { position: absolute; left: 0.9rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); width: 15px; height: 15px; pointer-events: none; }
.search-input { width: 100%; padding: 0.68rem 1rem 0.68rem 2.5rem; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: var(--radius-btn); color: var(--text-primary); font-family: inherit; font-size: 0.875rem; outline: none; transition: var(--transition); }
.search-input::placeholder { color: var(--text-muted); }
.search-input:focus { border-color: rgba(77,184,255,0.45); background: var(--bg-glass-hover); box-shadow: 0 0 0 3px rgba(77,184,255,0.1); }

.custom-select-wrap { position: relative; }
.custom-select-trigger { display: flex; align-items: center; gap: 0.45rem; padding: 0.68rem 0.875rem; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: var(--radius-btn); color: var(--text-primary); font-family: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: var(--transition); white-space: nowrap; user-select: none; min-width: 140px; }
.custom-select-trigger:hover { border-color: rgba(77,184,255,0.35); background: var(--bg-glass-hover); }
.custom-select-trigger.open { border-color: rgba(77,184,255,0.45); box-shadow: 0 0 0 3px rgba(77,184,255,0.1); }
.custom-select-trigger .arr-icon { width: 13px; height: 13px; margin-left: auto; color: var(--text-muted); transition: transform 0.18s; flex-shrink: 0; }
.custom-select-trigger.open .arr-icon { transform: rotate(180deg); }
.custom-select-dropdown { position: absolute; top: calc(100% + 5px); left: 0; min-width: 100%; background: rgba(20,24,34,0.98); backdrop-filter: blur(20px); border: 1px solid var(--border-glass); border-radius: var(--radius-btn); overflow: hidden; z-index: 700; box-shadow: 0 12px 40px rgba(0,0,0,0.55); opacity: 0; transform: translateY(-6px); pointer-events: none; transition: all 0.16s cubic-bezier(0.4,0,0.2,1); }
.custom-select-dropdown.open { opacity: 1; transform: translateY(0); pointer-events: all; }
.custom-select-option { padding: 0.6rem 0.875rem; font-size: 0.82rem; font-weight: 500; cursor: pointer; transition: background 0.1s; color: var(--text-secondary); }
.custom-select-option:hover { background: var(--bg-glass); color: var(--text-primary); }
.custom-select-option.selected { color: var(--accent-light); background: rgba(77,184,255,0.1); }

.color-picker-wrap { position: relative; }
.color-trigger { display: flex; align-items: center; gap: 0.5rem; padding: 0.68rem 0.875rem; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: var(--radius-btn); color: var(--text-primary); font-family: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: var(--transition); white-space: nowrap; user-select: none; }
.color-trigger:hover { border-color: rgba(77,184,255,0.35); background: var(--bg-glass-hover); }
.color-swatch-preview { width: 18px; height: 18px; border-radius: 5px; border: 1.5px solid rgba(255,255,255,0.18); flex-shrink: 0; transition: background 0.2s; }

.color-panel { position: absolute; top: calc(100% + 5px); right: 0; width: 280px; background: rgba(18,22,32,0.98); backdrop-filter: blur(24px); border: 1px solid var(--border-glass); border-radius: 14px; padding: 1rem; z-index: 600; box-shadow: 0 16px 48px rgba(0,0,0,0.6); opacity: 0; transform: translateY(-8px); pointer-events: none; transition: all 0.18s cubic-bezier(0.4,0,0.2,1); }
.color-panel.open { opacity: 1; transform: translateY(0); pointer-events: all; }

.hsv-canvas-wrap { position: relative; width: 100%; padding-bottom: 60%; border-radius: 8px; overflow: hidden; margin-bottom: 0.6rem; cursor: crosshair; }
.hsv-canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; border-radius: 8px; }
.hsv-cursor { position: absolute; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px rgba(0,0,0,0.4); transform: translate(-50%,-50%); pointer-events: none; top: 10%; left: 80%; }

.hue-bar-wrap { position: relative; height: 14px; border-radius: 7px; background: linear-gradient(to right,#f00,#ff0,#0f0,#0ff,#00f,#f0f,#f00); margin-bottom: 0.6rem; cursor: pointer; overflow: visible; }
.hue-thumb { position: absolute; top: 50%; transform: translate(-50%,-50%); width: 18px; height: 18px; border-radius: 50%; border: 2.5px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.5); pointer-events: none; left: 0%; }

.color-hex-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.3rem; }
.color-hex-label { font-size: 0.72rem; color: var(--text-muted); font-weight: 700; flex-shrink: 0; }
.color-hex-input { flex: 1; padding: 0.4rem 0.6rem; background: rgba(255,255,255,0.06); border: 1px solid var(--border-glass); border-radius: 7px; color: var(--text-primary); font-family: inherit; font-size: 0.78rem; outline: none; transition: border-color 0.15s; }
.color-hex-input:focus { border-color: rgba(77,184,255,0.45); }
.color-preview-dot { width: 26px; height: 26px; border-radius: 7px; border: 1.5px solid rgba(255,255,255,0.15); flex-shrink: 0; }

.results-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; padding: 0 0.1rem; }
.results-count { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
.results-count span { color: var(--accent-light); font-weight: 700; }

.icon-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(120px,1fr)); gap: 0.75rem; }
.icon-card { background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: var(--radius-card); padding: 1.25rem 0.6rem 0.875rem; display: flex; flex-direction: column; align-items: center; text-align: center; cursor: pointer; transition: var(--transition); position: relative; overflow: hidden; }
.icon-card::before { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg,rgba(77,184,255,0.05) 0%,transparent 60%); opacity: 0; transition: opacity 0.2s; border-radius: var(--radius-card); }
.icon-card:hover { transform: translateY(-3px); border-color: var(--border-hover); box-shadow: 0 8px 28px rgba(77,184,255,0.14); background: var(--bg-glass-hover); }
.icon-card:hover::before { opacity: 1; }
.icon-card-fav { position: absolute; top: 0.5rem; right: 0.5rem; width: 24px; height: 24px; border-radius: 7px; display: flex; align-items: center; justify-content: center; background: transparent; border: none; cursor: pointer; transition: var(--transition); z-index: 2; color: var(--text-muted); }
.icon-card-fav:hover { color: #f43f5e; background: rgba(244,63,94,0.12); }
.icon-card-fav.active { color: #f43f5e; }
.icon-card-fav svg { width: 13px; height: 13px; }
.icon-card-svg { display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; width: 42px; height: 42px; flex-shrink: 0; }
.icon-card-svg svg { width: 32px; height: 32px; transition: transform 0.2s; color: var(--icon-color); fill: currentColor; }
.icon-card:hover .icon-card-svg svg { transform: scale(1.1); }
.icon-card-name { font-size: 0.68rem; font-weight: 500; color: var(--text-muted); word-break: break-all; line-height: 1.35; transition: color 0.2s; }
.icon-card:hover .icon-card-name { color: var(--text-secondary); }
.no-results { grid-column: 1/-1; text-align: center; padding: 4rem 2rem; color: var(--text-muted); }
.no-results svg { width: 44px; height: 44px; margin-bottom: 0.75rem; opacity: 0.3; }
.no-results p { font-size: 0.95rem; font-weight: 500; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.78); backdrop-filter: blur(14px); z-index: 2000; display: flex; align-items: center; justify-content: center; padding: 1rem; opacity: 0; pointer-events: none; transition: opacity 0.22s; }
.modal-overlay.open { opacity: 1; pointer-events: all; }
.modal { background: rgba(18,22,32,0.97); border: 1px solid var(--border-glass); border-radius: 18px; width: 100%; max-width: 500px; max-height: 92vh; overflow-y: auto; box-shadow: 0 24px 72px rgba(0,0,0,0.65); transform: translateY(18px) scale(0.97); transition: transform 0.25s cubic-bezier(0.4,0,0.2,1); scrollbar-width: thin; scrollbar-color: var(--border-glass) transparent; }
.modal-overlay.open .modal { transform: translateY(0) scale(1); }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 1.1rem 1.25rem 0; }
.modal-title { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }
.modal-close { width: 30px; height: 30px; border-radius: 8px; background: var(--bg-glass); border: 1px solid var(--border-glass); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: var(--transition); color: var(--text-secondary); }
.modal-close:hover { background: rgba(244,63,94,0.15); border-color: rgba(244,63,94,0.3); color: #f43f5e; }
.modal-close svg { width: 13px; height: 13px; }
.modal-preview { display: flex; flex-direction: column; align-items: center; padding: 1.75rem 1.25rem 1.25rem; gap: 0.875rem; }
.modal-icon-wrap { width: 110px; height: 110px; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: 18px; display: flex; align-items: center; justify-content: center; }
.modal-icon-wrap svg { width: 66px; height: 66px; fill: currentColor; transition: color 0.2s; }
.modal-icon-name { font-size: 1rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em; text-align: center; word-break: break-all; }

/* Modal CDN Tag Box */
.modal-cdn-box { background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); border-radius: 10px; padding: 0.85rem; margin-bottom: 1.25rem; width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.modal-cdn-box code { font-family: monospace; color: #a5b4fc; font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.modal-cdn-btn { background: rgba(77,184,255,0.1); border: 1px solid rgba(77,184,255,0.3); color: #4db8ff; padding: 0.35rem 0.65rem; border-radius: 6px; cursor: pointer; font-size: 0.7rem; font-weight: 700; transition: var(--transition); flex-shrink: 0; }
.modal-cdn-btn:hover { background: rgba(77,184,255,0.2); }

.modal-body { padding: 0 1.25rem 1.25rem; }
.modal-section { margin-bottom: 1.1rem; }
.modal-section-label { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }

.size-row { display: flex; align-items: center; gap: 0.75rem; }
.size-display { min-width: 52px; text-align: center; padding: 0.45rem 0.6rem; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: 7px; font-size: 0.8rem; font-weight: 700; color: var(--accent-light); font-family: inherit; }
.size-slider-wrap { flex: 1; display: flex; align-items: center; }
.size-slider { width: 100%; height: 6px; -webkit-appearance: none; appearance: none; background: linear-gradient(to right,var(--accent) 0%,var(--accent) var(--pct,25%),rgba(255,255,255,0.1) var(--pct,25%)); border-radius: 3px; outline: none; cursor: pointer; }
.size-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%; background: #fff; border: 2px solid var(--accent); box-shadow: 0 2px 8px rgba(77,184,255,0.4); cursor: pointer; transition: transform 0.15s; }
.size-slider::-webkit-slider-thumb:hover { transform: scale(1.2); }

.modal-color-card { background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: 12px; padding: 0.875rem; }
.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 1.1rem; }
.action-btn { padding: 0.65rem 0.4rem; border-radius: var(--radius-btn); font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: var(--transition); border: 1px solid; display: flex; align-items: center; justify-content: center; gap: 0.35rem; }
.action-btn svg { width: 13px; height: 13px; flex-shrink: 0; }
.btn-dl-svg { background: linear-gradient(135deg,#4db8ff,#7c6fff); border-color: transparent; color: #fff; box-shadow: 0 4px 14px rgba(77,184,255,0.3); }
.btn-dl-svg:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(77,184,255,0.45); }
.btn-dl-png { background: linear-gradient(135deg,#7c6fff,#a855f7); border-color: transparent; color: #fff; box-shadow: 0 4px 14px rgba(124,111,255,0.3); }
.btn-dl-png:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(124,111,255,0.45); }
.btn-cp-svg { background: var(--bg-glass); border-color: var(--border-glass); color: var(--text-secondary); }
.btn-cp-svg:hover { border-color: rgba(77,184,255,0.4); color: var(--accent-light); background: var(--bg-glass-hover); }
.btn-cp-png { background: var(--bg-glass); border-color: var(--border-glass); color: var(--text-secondary); }
.btn-cp-png:hover { border-color: rgba(77,184,255,0.4); color: var(--accent-light); background: var(--bg-glass-hover); }

.sidebar-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 1500; opacity: 0; pointer-events: none; transition: opacity 0.22s; }
.sidebar-overlay.open { opacity: 1; pointer-events: all; }
.sidebar { position: fixed; top: 0; right: 0; height: 100%; width: 320px; max-width: 90vw; background: rgba(15,19,28,0.98); backdrop-filter: blur(24px); border-left: 1px solid var(--border-glass); z-index: 1600; transform: translateX(100%); transition: transform 0.28s cubic-bezier(0.4,0,0.2,1); display: flex; flex-direction: column; box-shadow: -12px 0 40px rgba(0,0,0,0.45); }
.sidebar.open { transform: translateX(0); }
.sidebar-header { padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--border-glass); display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.sidebar-title-wrap { display: flex; align-items: center; gap: 0.5rem; }
.sidebar-title { font-size: 0.95rem; font-weight: 700; color: var(--text-primary); }
.sidebar-badge { background: linear-gradient(135deg,#4db8ff,#7c6fff); color: #fff; border-radius: 9999px; font-size: 0.7rem; font-weight: 700; padding: 2px 7px; }
.sidebar-close { width: 30px; height: 30px; border-radius: 8px; background: var(--bg-glass); border: 1px solid var(--border-glass); display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-secondary); transition: var(--transition); }
.sidebar-close:hover { background: rgba(244,63,94,0.15); color: #f43f5e; }
.sidebar-close svg { width: 13px; height: 13px; }
.sidebar-body { flex: 1; overflow-y: auto; padding: 0.875rem; scrollbar-width: thin; scrollbar-color: var(--border-glass) transparent; }
.sidebar-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-muted); padding: 2rem; text-align: center; gap: 0.65rem; }
.sidebar-empty svg { width: 36px; height: 36px; opacity: 0.28; }
.sidebar-empty p { font-size: 0.82rem; font-weight: 500; }
.bucket-list { display: flex; flex-direction: column; gap: 0.45rem; }
.bucket-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.75rem; background: var(--bg-glass); border: 1px solid var(--border-glass); border-radius: 11px; transition: var(--transition); cursor: pointer; }
.bucket-item:hover { border-color: rgba(77,184,255,0.3); background: var(--bg-glass-hover); }
.bucket-item-icon { width: 32px; height: 32px; background: rgba(77,184,255,0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.bucket-item-icon svg { width: 18px; height: 18px; fill: currentColor; color: var(--icon-color); }
.bucket-item-name { flex: 1; font-size: 0.77rem; font-weight: 500; color: var(--text-secondary); word-break: break-all; line-height: 1.3; }
.bucket-item-remove { width: 22px; height: 22px; border-radius: 6px; background: transparent; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-muted); transition: var(--transition); flex-shrink: 0; padding: 0; }
.bucket-item-remove:hover { background: rgba(244,63,94,0.15); color: #f43f5e; }
.bucket-item-remove svg { width: 11px; height: 11px; }

.toast-container { position: fixed; bottom: 1.75rem; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex; flex-direction: column; align-items: center; gap: 0.4rem; pointer-events: none; }
.toast { background: rgba(18,22,32,0.96); backdrop-filter: blur(14px); border: 1px solid var(--border-glass); border-radius: 11px; padding: 0.6rem 1.1rem; font-size: 0.82rem; font-weight: 600; color: var(--text-primary); box-shadow: 0 8px 28px rgba(0,0,0,0.45); animation: toastIn 0.26s cubic-bezier(0.34,1.56,0.64,1) forwards; display: flex; align-items: center; gap: 0.45rem; white-space: nowrap; }
.toast.hiding { animation: toastOut 0.2s ease forwards; }
.toast-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; flex-shrink: 0; }
.toast-dot.warn { background: #f59e0b; }
.toast-dot.info { background: #4db8ff; }
@keyframes toastIn { from { opacity:0; transform:translateY(10px) scale(0.94); } to { opacity:1; transform:translateY(0) scale(1); } }
@keyframes toastOut { from { opacity:1; transform:translateY(0) scale(1); } to { opacity:0; transform:translateY(-7px) scale(0.94); } }

/* Mobile CDN CSS addition */
@media (max-width: 640px) {
    main { padding-left: 0.75rem; padding-right: 0.75rem; }
    nav { padding: 0 0.875rem; }
    .cat-bar-outer { padding: 0 0.75rem; }
    .toolbar { gap: 0.5rem; }
    .icon-grid { grid-template-columns: repeat(4,1fr); gap: 0.5rem; }
    .icon-card { padding: 1rem 0.35rem 0.65rem; border-radius: 11px; }
    .icon-card-svg svg { width: 26px; height: 26px; }
    .icon-card-name { font-size: 0.62rem; }
    .icon-card-fav { width: 20px; height: 20px; top: 0.25rem; right: 0.25rem; }
    .icon-card-fav svg { width: 11px; height: 11px; }
    .search-wrap { min-width: 100%; order: -1; flex: 0 0 100%; }
    .color-panel { right: auto; left: 0; width: 260px; }
    .docs-code { flex-direction: column; align-items: stretch; gap: 0.5rem; }
    .copy-docs-btn { text-align: center; }
    .cdn-nav-btn .desktop-text { display: none !important; }
    .cdn-nav-btn .mobile-text { display: inline !important; }
}
canvas#pngCanvas { display: none; }

/* ── CDN Button in Nav ── */
.cdn-nav-btn {
    display: flex; align-items: center; gap: 0.45rem;
    padding: 0.45rem 1rem;
    background: linear-gradient(135deg, rgba(124,111,255,0.18), rgba(77,184,255,0.12));
    border: 1px solid rgba(124,111,255,0.35);
    border-radius: 9999px;
    color: #b8b0ff;
    font-family: inherit; font-size: 0.82rem; font-weight: 600;
    cursor: pointer; transition: var(--transition);
    white-space: nowrap;
}
.cdn-nav-btn:hover {
    background: linear-gradient(135deg, rgba(124,111,255,0.3), rgba(77,184,255,0.2));
    border-color: rgba(124,111,255,0.6);
    transform: translateY(-1px);
}
.cdn-nav-btn svg { width: 14px; height: 14px; flex-shrink: 0; }
.cdn-nav-btn .mobile-text { display: none; }

/* ── CDN Modal ── */
.cdn-modal-overlay {
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.82);
    backdrop-filter: blur(18px);
    z-index: 3000;
    display: flex; align-items: center; justify-content: center;
    padding: 1rem;
    opacity: 0; pointer-events: none;
    transition: opacity 0.22s;
}
.cdn-modal-overlay.open { opacity: 1; pointer-events: all; }

.cdn-modal {
    background: rgba(14,18,28,0.98);
    border: 1px solid rgba(124,111,255,0.22);
    border-radius: 20px;
    width: 100%; max-width: 680px;
    max-height: 90vh;
    overflow: hidden;
    display: flex; flex-direction: column;
    box-shadow: 0 32px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(77,184,255,0.07);
    transform: translateY(20px) scale(0.97);
    transition: transform 0.28s cubic-bezier(0.34,1.2,0.64,1);
}
.cdn-modal-overlay.open .cdn-modal { transform: translateY(0) scale(1); }

.cdn-modal-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.25rem 1.5rem 0;
    flex-shrink: 0;
}
.cdn-modal-title-group { display: flex; align-items: center; gap: 0.75rem; }
.cdn-modal-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, rgba(124,111,255,0.25), rgba(77,184,255,0.18));
    border: 1px solid rgba(124,111,255,0.3);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.cdn-modal-icon svg { width: 17px; height: 17px; color: #b8b0ff; }
.cdn-modal-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em; }
.cdn-modal-subtitle { font-size: 0.75rem; color: var(--text-muted); margin-top: 1px; }

.cdn-modal-close {
    width: 30px; height: 30px; border-radius: 8px;
    background: var(--bg-glass); border: 1px solid var(--border-glass);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: var(--transition); color: var(--text-secondary);
    flex-shrink: 0;
}
.cdn-modal-close:hover { background: rgba(244,63,94,0.15); border-color: rgba(244,63,94,0.3); color: #f43f5e; }
.cdn-modal-close svg { width: 13px; height: 13px; }

/* CDN URL Hero */
.cdn-url-hero {
    margin: 1.25rem 1.5rem 0;
    background: linear-gradient(135deg, rgba(77,184,255,0.06), rgba(124,111,255,0.06));
    border: 1px solid rgba(77,184,255,0.18);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    flex-shrink: 0;
}
.cdn-url-label {
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 0.6rem;
    display: flex; align-items: center; gap: 0.4rem;
}
.cdn-url-label::before { content: ''; width: 6px; height: 6px; background: var(--accent); border-radius: 50%; display: inline-block; }
.cdn-url-row { display: flex; align-items: center; gap: 0.5rem; }
.cdn-url-text {
    flex: 1; padding: 0.6rem 0.875rem;
    background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 9px; font-size: 0.82rem; font-weight: 600;
    color: var(--accent-light); font-family: 'Courier New', monospace;
    word-break: break-all; line-height: 1.5;
}
.cdn-copy-btn {
    flex-shrink: 0; padding: 0.6rem 0.875rem;
    background: linear-gradient(135deg, #4db8ff, #7c6fff);
    border: none; border-radius: 9px;
    color: #fff; font-family: inherit; font-size: 0.78rem; font-weight: 700;
    cursor: pointer; transition: var(--transition);
    display: flex; align-items: center; gap: 0.35rem; white-space: nowrap;
}
.cdn-copy-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(77,184,255,0.4); }
.cdn-copy-btn svg { width: 12px; height: 12px; }

/* CDN Tabs */
.cdn-tabs-wrap {
    display: flex; gap: 0; padding: 1rem 1.5rem 0;
    border-bottom: 1px solid var(--border-glass);
    flex-shrink: 0; overflow-x: auto; scrollbar-width: none;
}
.cdn-tabs-wrap::-webkit-scrollbar { display: none; }
.cdn-tab {
    padding: 0.5rem 1rem;
    font-family: inherit; font-size: 0.8rem; font-weight: 600;
    color: var(--text-muted); background: none; border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer; transition: color 0.18s, border-color 0.18s;
    white-space: nowrap; margin-bottom: -1px;
}
.cdn-tab:hover { color: var(--text-secondary); }
.cdn-tab.active { color: var(--accent-light); border-bottom-color: var(--accent); }

/* CDN Scroll Body */
.cdn-modal-body {
    flex: 1; overflow-y: auto;
    padding: 1.25rem 1.5rem 1.5rem;
    scrollbar-width: thin;
    scrollbar-color: var(--border-glass) transparent;
}

.cdn-tab-content { display: none; }
.cdn-tab-content.active { display: block; }

/* Code blocks */
.cdn-section { margin-bottom: 1.5rem; }
.cdn-section:last-child { margin-bottom: 0; }
.cdn-section-label {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--text-muted); margin-bottom: 0.6rem;
}
.cdn-code-block {
    position: relative;
    background: rgba(0,0,0,0.4);
    border: 1px solid var(--border-glass);
    border-radius: 11px; overflow: hidden;
}
.cdn-code-lang {
    position: absolute; top: 0.6rem; right: 0.6rem;
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em;
    color: var(--text-muted); text-transform: uppercase;
    background: rgba(255,255,255,0.06);
    padding: 2px 7px; border-radius: 5px;
}
.cdn-code-copy {
    position: absolute; top: 0.5rem; right: 3.5rem;
    padding: 3px 8px;
    background: rgba(77,184,255,0.12); border: 1px solid rgba(77,184,255,0.25);
    border-radius: 6px; color: var(--accent-light);
    font-family: inherit; font-size: 0.65rem; font-weight: 700;
    cursor: pointer; transition: var(--transition);
}
.cdn-code-copy:hover { background: rgba(77,184,255,0.22); }
.cdn-code-block pre {
    margin: 0; padding: 1rem 1.1rem;
    font-size: 0.78rem; line-height: 1.7;
    color: #c9d1e0; font-family: 'Courier New', Courier, monospace;
    overflow-x: auto; white-space: pre;
}
.cdn-code-block code .kw  { color: #7c6fff; }  /* keyword / tag */
.cdn-code-block code .st  { color: #4db8ff; }  /* string */
.cdn-code-block code .cm  { color: #4a5568; font-style: italic; } /* comment */
.cdn-code-block code .at  { color: #80cfff; }  /* attribute */
.cdn-code-block code .fn  { color: #a78bfa; }  /* function */
.cdn-code-block code .nu  { color: #f59e0b; }  /* number */

/* Info note */
.cdn-note {
    display: flex; gap: 0.65rem; align-items: flex-start;
    background: rgba(77,184,255,0.06);
    border: 1px solid rgba(77,184,255,0.15);
    border-radius: 10px; padding: 0.75rem 1rem;
    margin-bottom: 1.25rem;
}
.cdn-note-icon { flex-shrink: 0; margin-top: 1px; }
.cdn-note-icon svg { width: 14px; height: 14px; color: var(--accent); }
.cdn-note-text { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.6; }
.cdn-note-text strong { color: var(--accent-light); }

/* Framework badge row */
.fw-badges { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1.1rem; }
.fw-badge {
    padding: 4px 10px; border-radius: 6px;
    font-size: 0.7rem; font-weight: 700;
    border: 1px solid;
}
.fw-badge.html  { background: rgba(244,116,0,0.1);  border-color: rgba(244,116,0,0.3);  color: #fb923c; }
.fw-badge.react { background: rgba(97,218,251,0.1); border-color: rgba(97,218,251,0.3); color: #67e8f9; }
.fw-badge.vue   { background: rgba(66,184,131,0.1); border-color: rgba(66,184,131,0.3); color: #4ade80; }
.fw-badge.svelte{ background: rgba(255,62,0,0.1);   border-color: rgba(255,62,0,0.3);   color: #f87171; }
.fw-badge.next  { background: rgba(255,255,255,0.06);border-color: rgba(255,255,255,0.15);color: #e2e8f0; }
.fw-badge.nuxt  { background: rgba(0,220,130,0.1);  border-color: rgba(0,220,130,0.3);  color: #34d399; }
.fw-badge.cdn   { background: rgba(77,184,255,0.1); border-color: rgba(77,184,255,0.3); color: #60c6ff; }

/* Modal also gets CDN tab section */
.modal-cdn-section {
    margin: 0 1.25rem 1.25rem;
    background: rgba(124,111,255,0.05);
    border: 1px solid rgba(124,111,255,0.15);
    border-radius: 12px;
    overflow: hidden;
}
.modal-cdn-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(124,111,255,0.1);
    cursor: pointer; transition: background 0.18s;
}
.modal-cdn-header:hover { background: rgba(124,111,255,0.06); }
.modal-cdn-header-title {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.78rem; font-weight: 700; color: #b8b0ff;
}
.modal-cdn-header-title svg { width: 13px; height: 13px; }
.modal-cdn-chevron { width: 14px; height: 14px; color: var(--text-muted); transition: transform 0.2s; }
.modal-cdn-chevron.open { transform: rotate(180deg); }
.modal-cdn-body { display: none; padding: 1rem; }
.modal-cdn-body.open { display: block; }

/* Mini tabs inside modal */
.mini-tabs { display: flex; gap: 0.35rem; flex-wrap: wrap; margin-bottom: 1rem; }
.mini-tab {
    padding: 4px 10px;
    background: var(--bg-glass); border: 1px solid var(--border-glass);
    border-radius: 6px; font-family: inherit; font-size: 0.72rem; font-weight: 600;
    color: var(--text-muted); cursor: pointer; transition: var(--transition);
}
.mini-tab:hover { color: var(--text-secondary); border-color: rgba(255,255,255,0.15); }
.mini-tab.active { background: rgba(77,184,255,0.15); border-color: rgba(77,184,255,0.35); color: var(--accent-light); }
.mini-code-panel { display: none; }
.mini-code-panel.active { display: block; }
.mini-code-block {
    position: relative;
    background: rgba(0,0,0,0.45);
    border: 1px solid var(--border-glass);
    border-radius: 9px; overflow: hidden;
}
.mini-code-block pre {
    margin: 0; padding: 0.75rem 0.9rem;
    font-size: 0.73rem; line-height: 1.65;
    color: #c9d1e0; font-family: 'Courier New', Courier, monospace;
    overflow-x: auto; white-space: pre;
}
.mini-copy-btn {
    position: absolute; top: 0.4rem; right: 0.4rem;
    padding: 3px 8px;
    background: rgba(77,184,255,0.12); border: 1px solid rgba(77,184,255,0.25);
    border-radius: 5px; color: var(--accent-light);
    font-family: inherit; font-size: 0.62rem; font-weight: 700;
    cursor: pointer; transition: var(--transition);
}
.mini-copy-btn:hover { background: rgba(77,184,255,0.22); }

@media (max-width: 640px) {
    .cdn-modal-head { padding: 1rem 1rem 0; }
    .cdn-url-hero { margin: 1rem 1rem 0; }
    .cdn-tabs-wrap { padding: 0.875rem 1rem 0; }
    .cdn-modal-body { padding: 1rem; }
    .cdn-modal { max-height: 95vh; }
    .cdn-nav-btn .desktop-text { display: none; }
    .cdn-nav-btn { padding: 0.45rem 0.7rem; }
    .modal-cdn-section { margin: 0 0.875rem 1rem; }
}
</style>
</head>
<body>
<div class="wrapper">

<nav>
    <a class="nav-brand" href="#">
        <div class="nav-logo">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </div>
        <span class="nav-title">{{ siteTitle }}</span>
    </a>
    <div class="nav-actions">
        <button class="cdn-nav-btn" id="cdnNavBtn" onclick="openCdnModal()">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            <span class="desktop-text">Use CDN</span>
            <span class="mobile-text">CDN</span>
        </button>
        <button class="bucket-btn" id="bucketBtn">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>
            My Bucket
            <span class="bucket-count" id="bucketCount">0</span>
        </button>
    </div>
</nav>

<div class="cat-bar-outer">
    <div class="cat-bar" id="catBar">
        {% for key, cat in CATEGORIES.items() %}
        <button class="cat-chip{{ ' active' if key == 'all' else '' }}" data-cat="{{ key }}">{{ cat.label }}</button>
        {% endfor %}
    </div>
</div>

<main>
    <div class="docs-section">
        <div class="docs-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4db8ff" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            How to Use the Public CDN
        </div>
        <p class="docs-text">Add the script tag below to your website's <code>&lt;head&gt;</code>. Then simply use <code>&lt;i data-icon="icon-name"&gt;&lt;/i&gt;</code> anywhere in your HTML to render an icon instantly.</p>
        <div class="docs-code">
            <span id="mainCdnScript">&lt;script src="{{ baseCdnUrl }}"&gt;&lt;/script&gt;</span>
            <button class="copy-docs-btn" onclick="copyMainCDN()">Copy Script</button>
        </div>
    </div>

    <div class="toolbar">
        <div class="search-wrap">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" class="search-input" id="searchInput" placeholder="Search {{ allIcons|length }} icons...">
        </div>
        <div class="custom-select-wrap" id="styleFilterWrap">
            <div class="custom-select-trigger" id="styleFilterTrigger">
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                <span id="styleFilterLabel">All Styles</span>
                <svg class="arr-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
            <div class="custom-select-dropdown" id="styleFilterDropdown">
                <div class="custom-select-option selected" data-value="">All Styles</div>
                <div class="custom-select-option" data-value="bold">Bold</div>
                <div class="custom-select-option" data-value="duotone">Duotone</div>
                <div class="custom-select-option" data-value="line-duotone">Line Duotone</div>
                <div class="custom-select-option" data-value="linear">Linear</div>
                <div class="custom-select-option" data-value="outline">Outline</div>
                <div class="custom-select-option" data-value="broken">Broken</div>
            </div>
        </div>
        <div class="color-picker-wrap" id="globalColorWrap">
            <div class="color-trigger" id="globalColorTrigger">
                <div class="color-swatch-preview" id="globalColorPreview"></div>
                Color
            </div>
            <div class="color-panel" id="globalColorPanel">
                <div class="hsv-canvas-wrap" id="globalHsvWrap">
                    <canvas class="hsv-canvas" id="globalHsvCanvas"></canvas>
                    <div class="hsv-cursor" id="globalHsvCursor"></div>
                </div>
                <div class="hue-bar-wrap" id="globalHueBar">
                    <div class="hue-thumb" id="globalHueThumb"></div>
                </div>
                <div class="color-hex-row">
                    <span class="color-hex-label">HEX</span>
                    <input type="text" class="color-hex-input" id="globalHexInput" maxlength="7" placeholder="#c8d6e8">
                    <div class="color-preview-dot" id="globalHexPreviewDot"></div>
                </div>
            </div>
        </div>
    </div>
    <div class="results-bar">
        <span class="results-count"><span id="visibleCount">{{ allIcons|length }}</span> icons</span>
    </div>
    <div class="icon-grid" id="iconGrid">
        {% if allIcons %}
            {% for iconName, iconDetails in allIcons.items() %}
                {% set svgBody = iconDetails.get('body', '') %}
                {% set svgStr = '<svg xmlns="http://www.w3.org/2000/svg" width="' ~ globalWidth ~ '" height="' ~ globalHeight ~ '" viewBox="0 0 ' ~ globalWidth ~ ' ' ~ globalHeight ~ '">' ~ svgBody ~ '</svg>' %}
                <div class="icon-card" data-name="{{ iconName|e }}" data-body="{{ svgBody|e }}" onclick="handleCardClick(event,this)">
                    <button class="icon-card-fav" data-name="{{ iconName|e }}" onclick="toggleFav(event,this)" title="Add to Bucket">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
                    </button>
                    <div class="icon-card-svg">{{ svgStr|safe }}</div>
                    <div class="icon-card-name">{{ iconName|e }}</div>
                </div>
            {% endfor %}
        {% else %}
            <div class="no-results">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <p>icons.json not found or empty</p>
            </div>
        {% endif %}
    </div>
</main>
</div>

<div class="modal-overlay" id="modalOverlay" onclick="handleModalOverlayClick(event)">
    <div class="modal" id="modal">
        <div class="modal-header">
            <span class="modal-title">Icon Details</span>
            <button class="modal-close" onclick="closeModal()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-preview">
            <div class="modal-icon-wrap" id="modalIconWrap"></div>
            <div class="modal-icon-name" id="modalIconName"></div>
        </div>
        
        <div class="modal-body">
            <div class="modal-cdn-box">
                <code id="modalIconCdnCode">&lt;i data-icon="..."&gt;&lt;/i&gt;</code>
                <button class="modal-cdn-btn" onclick="copyIconCDNCode()">Copy Tag</button>
            </div>

            <div class="modal-section">
                <div class="modal-section-label">Export Size</div>
                <div class="size-row">
                    <div class="size-display" id="sizeDisplay">512px</div>
                    <div class="size-slider-wrap">
                        <input type="range" class="size-slider" id="modalSizeSlider" min="16" max="2048" value="512" step="8">
                    </div>
                </div>
            </div>
            <div class="modal-section">
                <div class="modal-section-label">Icon Color</div>
                <div class="modal-color-card">
                    <div class="hsv-canvas-wrap" id="modalHsvWrap">
                        <canvas class="hsv-canvas" id="modalHsvCanvas"></canvas>
                        <div class="hsv-cursor" id="modalHsvCursor"></div>
                    </div>
                    <div class="hue-bar-wrap" id="modalHueBar">
                        <div class="hue-thumb" id="modalHueThumb"></div>
                    </div>
                    <div class="color-hex-row">
                        <span class="color-hex-label">HEX</span>
                        <input type="text" class="color-hex-input" id="modalHexInput" maxlength="7" placeholder="#c8d6e8">
                        <div class="color-preview-dot" id="modalHexPreviewDot"></div>
                    </div>
                </div>
            </div>
            <div class="modal-section">
                <div class="modal-section-label">Use via CDN</div>
                <div class="modal-cdn-section">
                    <div class="modal-cdn-header" onclick="toggleModalCdn(this)">
                        <span class="modal-cdn-header-title">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                            CDN Usage Code
                        </span>
                        <svg class="modal-cdn-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                    </div>
                    <div class="modal-cdn-body" id="modalCdnBody">
                        <div class="mini-tabs" id="miniTabBar">
                            <button class="mini-tab active" data-minitab="html">HTML</button>
                            <button class="mini-tab" data-minitab="react">React</button>
                            <button class="mini-tab" data-minitab="vue">Vue</button>
                            <button class="mini-tab" data-minitab="svelte">Svelte</button>
                            <button class="mini-tab" data-minitab="next">Next.js</button>
                        </div>
                        <div id="miniHtml" class="mini-code-panel active">
                            <div class="mini-code-block">
                                <button class="mini-copy-btn" onclick="miniCopy('miniHtmlCode')">Copy</button>
                                <pre><code id="miniHtmlCode"></code></pre>
                            </div>
                        </div>
                        <div id="miniReact" class="mini-code-panel">
                            <div class="mini-code-block">
                                <button class="mini-copy-btn" onclick="miniCopy('miniReactCode')">Copy</button>
                                <pre><code id="miniReactCode"></code></pre>
                            </div>
                        </div>
                        <div id="miniVue" class="mini-code-panel">
                            <div class="mini-code-block">
                                <button class="mini-copy-btn" onclick="miniCopy('miniVueCode')">Copy</button>
                                <pre><code id="miniVueCode"></code></pre>
                            </div>
                        </div>
                        <div id="miniSvelte" class="mini-code-panel">
                            <div class="mini-code-block">
                                <button class="mini-copy-btn" onclick="miniCopy('miniSvelteCode')">Copy</button>
                                <pre><code id="miniSvelteCode"></code></pre>
                            </div>
                        </div>
                        <div id="miniNext" class="mini-code-panel">
                            <div class="mini-code-block">
                                <button class="mini-copy-btn" onclick="miniCopy('miniNextCode')">Copy</button>
                                <pre><code id="miniNextCode"></code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-actions">
                <button class="action-btn btn-dl-svg" onclick="downloadSVG()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download SVG</button>
                <button class="action-btn btn-dl-png" onclick="downloadPNG()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>Download PNG</button>
                <button class="action-btn btn-cp-svg" onclick="copySVG()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Copy SVG</button>
                <button class="action-btn btn-cp-png" onclick="copyPNG()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>Copy PNG</button>
            </div>
        </div>
    </div>
</div>

<div class="sidebar-overlay" id="sidebarOverlay" onclick="closeSidebar()"></div>
<div class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <div class="sidebar-title-wrap">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>
            <span class="sidebar-title">My Bucket</span>
            <span class="sidebar-badge" id="sidebarBadge">0</span>
        </div>
        <button class="sidebar-close" onclick="closeSidebar()"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="sidebar-body" id="sidebarBody"></div>
</div>

<div class="toast-container" id="toastContainer"></div>
<canvas id="pngCanvas"></canvas>


<div class="cdn-modal-overlay" id="cdnModalOverlay" onclick="handleCdnOverlayClick(event)">
    <div class="cdn-modal">

        <div class="cdn-modal-head">
            <div class="cdn-modal-title-group">
                <div class="cdn-modal-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                </div>
                <div>
                    <div class="cdn-modal-title">CDN Integration Docs</div>
                    <div class="cdn-modal-subtitle">Drop one &lt;script&gt; tag → icons render everywhere</div>
                </div>
            </div>
            <button class="cdn-modal-close" onclick="closeCdnModal()">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
        </div>

        <div class="cdn-url-hero">
            <div class="cdn-url-label">Drop into &lt;head&gt; — done</div>
            <div class="cdn-url-row">
                <div class="cdn-url-text" id="cdnBaseUrl">&lt;script src="{{ baseCdnUrl }}" defer&gt;&lt;/script&gt;</div>
                <button class="cdn-copy-btn" onclick="copyCdnUrl()">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                    Copy
                </button>
            </div>
        </div>

        <div class="cdn-tabs-wrap">
            <button class="cdn-tab active" data-cdntab="quickstart">Quick Start</button>
            <button class="cdn-tab" data-cdntab="react">React</button>
            <button class="cdn-tab" data-cdntab="vue">Vue 3</button>
            <button class="cdn-tab" data-cdntab="svelte">Svelte</button>
            <button class="cdn-tab" data-cdntab="next">Next.js</button>
            <button class="cdn-tab" data-cdntab="nuxt">Nuxt 3</button>
            <button class="cdn-tab" data-cdntab="api">API Ref</button>
        </div>

        <div class="cdn-modal-body">

            <div class="cdn-tab-content active" data-cdncontent="quickstart">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">Works like <strong>Font Awesome CDN</strong>. Add one script tag to <strong>&lt;head&gt;</strong>, then use <strong>data-icon=""</strong> anywhere in your HTML. Icons render automatically — no build tools, no npm.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge html">HTML</span><span class="fw-badge cdn">Vanilla JS</span><span class="fw-badge next">WordPress</span><span class="fw-badge html">Static Sites</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Step 1 — Add to &lt;head&gt;</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">html</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>&lt;<span class="kw">head</span>&gt;
  &lt;<span class="kw">script</span> <span class="at">src</span>=<span class="st">"{{ baseCdnUrl }}"</span> <span class="at">defer</span>&gt;&lt;/<span class="kw">script</span>&gt;
&lt;/<span class="kw">head</span>&gt;</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Step 2 — Use icons anywhere in body</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">html</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="cm">&lt;!-- Basic usage --&gt;</span>
&lt;<span class="kw">i</span> <span class="at">data-icon</span>=<span class="st">"home-smile"</span>&gt;&lt;/<span class="kw">i</span>&gt;

<span class="cm">&lt;!-- Custom size (px) --&gt;</span>
&lt;<span class="kw">i</span> <span class="at">data-icon</span>=<span class="st">"arrow-right"</span> <span class="at">data-size</span>=<span class="st">"32"</span>&gt;&lt;/<span class="kw">i</span>&gt;

<span class="cm">&lt;!-- Custom color via CSS --&gt;</span>
&lt;<span class="kw">i</span> <span class="at">data-icon</span>=<span class="st">"heart"</span> <span class="at">data-size</span>=<span class="st">"28"</span> <span class="at">style</span>=<span class="st">"color:#f43f5e"</span>&gt;&lt;/<span class="kw">i</span>&gt;

<span class="cm">&lt;!-- data-color attribute --&gt;</span>
&lt;<span class="kw">i</span> <span class="at">data-icon</span>=<span class="st">"star"</span> <span class="at">data-size</span>=<span class="st">"24"</span> <span class="at">data-color</span>=<span class="st">"#f59e0b"</span>&gt;&lt;/<span class="kw">i</span>&gt;</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">That's it. Full example</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">html</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>&lt;!DOCTYPE html&gt;
&lt;<span class="kw">html</span>&gt;
&lt;<span class="kw">head</span>&gt;
  &lt;<span class="kw">script</span> <span class="at">src</span>=<span class="st">"{{ baseCdnUrl }}"</span> <span class="at">defer</span>&gt;&lt;/<span class="kw">script</span>&gt;
&lt;/<span class="kw">head</span>&gt;
&lt;<span class="kw">body</span>&gt;
  &lt;<span class="kw">h1</span>&gt;
    &lt;<span class="kw">i</span> <span class="at">data-icon</span>=<span class="st">"home-smile"</span> <span class="at">data-size</span>=<span class="st">"28"</span> <span class="at">style</span>=<span class="st">"color:#4db8ff"</span>&gt;&lt;/<span class="kw">i</span>&gt;
    Welcome
  &lt;/<span class="kw">h1</span>&gt;
  &lt;<span class="kw">button</span>&gt;
    &lt;<span class="kw">i</span> <span class="at">data-icon</span>=<span class="st">"arrow-right"</span> <span class="at">data-size</span>=<span class="st">"18"</span>&gt;&lt;/<span class="kw">i</span>&gt;
    Next
  &lt;/<span class="kw">button</span>&gt;
&lt;/<span class="kw">body</span>&gt;
&lt;/<span class="kw">html</span>&gt;</code></pre>
                    </div>
                </div>
            </div>

            <div class="cdn-tab-content" data-cdncontent="react">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">Reusable <strong>&lt;MdIcon /&gt;</strong> component. Fetches each icon on-demand from <strong>cdn.php?icon=NAME</strong> — no bulk JSON download, built-in memory cache.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge react">React 18+</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">components/MdIcon.jsx</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">jsx</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="kw">import</span> { useState, useEffect, useRef } <span class="kw">from</span> <span class="st">'react'</span>;

<span class="kw">const</span> CDN  = <span class="st">'{{ baseCdnUrl }}'</span>;
<span class="kw">const</span> cache = {};

<span class="kw">export default function</span> <span class="fn">MdIcon</span>({ name, size = <span class="nu">24</span>, color = <span class="st">'currentColor'</span>, className = <span class="st">''</span> }) {
  <span class="kw">const</span> [svg, setSvg] = <span class="fn">useState</span>(<span class="st">''</span>);

  <span class="fn">useEffect</span>(() =&gt; {
    <span class="kw">if</span> (!name) <span class="kw">return</span>;
    <span class="kw">if</span> (cache[name]) { setSvg(cache[name]); <span class="kw">return</span>; }
    <span class="fn">fetch</span>(<span class="st">`${CDN}?icon=${encodeURIComponent(name)}&size=${size}`</span>)
      .<span class="fn">then</span>(r =&gt; r.<span class="fn">text</span>())
      .<span class="fn">then</span>(s =&gt; { cache[name] = s; setSvg(s); });
  }, [name, size]);

  <span class="kw">if</span> (!svg) <span class="kw">return</span> <span class="kw">null</span>;
  <span class="kw">return</span> (
    &lt;<span class="kw">span</span>
      className={className}
      style={{ color, display:<span class="st">'inline-flex'</span>, alignItems:<span class="st">'center'</span> }}
      dangerouslySetInnerHTML={{ __html: svg }}
    /&gt;
  );
}</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Usage</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">jsx</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="kw">import</span> MdIcon <span class="kw">from</span> <span class="st">'./components/MdIcon'</span>;

<span class="kw">export default function</span> <span class="fn">App</span>() {
  <span class="kw">return</span> (
    &lt;<span class="kw">div</span>&gt;
      &lt;<span class="fn">MdIcon</span> name=<span class="st">"home-smile"</span> size={<span class="nu">32</span>} color=<span class="st">"#4db8ff"</span> /&gt;
      &lt;<span class="fn">MdIcon</span> name=<span class="st">"arrow-right"</span> size={<span class="nu">20</span>} /&gt;
      &lt;<span class="fn">MdIcon</span> name=<span class="st">"heart"</span>       size={<span class="nu">24</span>} color=<span class="st">"#f43f5e"</span> /&gt;
    &lt;/<span class="kw">div</span>&gt;
  );
}</code></pre>
                    </div>
                </div>
            </div>

            <div class="cdn-tab-content" data-cdncontent="vue">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">Vue 3 Composition API component — fetches SVG directly from <strong>cdn.php?icon=NAME</strong> and injects it safely.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge vue">Vue 3</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">components/MdIcon.vue</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">vue</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>&lt;<span class="kw">script setup</span>&gt;
<span class="kw">import</span> { ref, watch, onMounted } <span class="kw">from</span> <span class="st">'vue'</span>;

<span class="kw">const</span> props = <span class="fn">defineProps</span>({
  name:  { type: String, required: <span class="kw">true</span> },
  size:  { type: Number, default: <span class="nu">24</span> },
  color: { type: String, default: <span class="st">'currentColor'</span> }
});

<span class="kw">const</span> CDN   = <span class="st">'{{ baseCdnUrl }}'</span>;
<span class="kw">const</span> cache = {};
<span class="kw">const</span> svg   = <span class="fn">ref</span>(<span class="st">''</span>);

<span class="kw">async function</span> <span class="fn">load</span>() {
  <span class="kw">if</span> (!props.name) <span class="kw">return</span>;
  <span class="kw">if</span> (cache[props.name]) { svg.value = cache[props.name]; <span class="kw">return</span>; }
  <span class="kw">const</span> res = <span class="kw">await</span> <span class="fn">fetch</span>(<span class="st">`${CDN}?icon=${props.name}&size=${props.size}`</span>);
  svg.value = cache[props.name] = <span class="kw">await</span> res.<span class="fn">text</span>();
}

<span class="fn">onMounted</span>(load);
<span class="fn">watch</span>(() =&gt; props.name, load);
&lt;/<span class="kw">script</span>&gt;

&lt;<span class="kw">template</span>&gt;
  &lt;<span class="kw">span</span> :<span class="at">style</span>=<span class="st">"`color:${color};display:inline-flex;align-items:center`"</span>
        v-html=<span class="st">"svg"</span> /&gt;
&lt;/<span class="kw">template</span>&gt;</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Usage</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">vue</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>&lt;<span class="kw">MdIcon</span> name=<span class="st">"home-smile"</span> :<span class="at">size</span>=<span class="st">"32"</span> color=<span class="st">"#4db8ff"</span> /&gt;
&lt;<span class="kw">MdIcon</span> name=<span class="st">"arrow-right"</span> /&gt;</code></pre>
                    </div>
                </div>
            </div>

            <div class="cdn-tab-content" data-cdncontent="svelte">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">Zero-dependency Svelte component — reactive, lightweight, fetches SVG on-demand.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge svelte">Svelte 4+</span><span class="fw-badge svelte">SvelteKit</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">lib/MdIcon.svelte</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">svelte</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>&lt;<span class="kw">script</span>&gt;
  <span class="kw">export let</span> name  = <span class="st">''</span>;
  <span class="kw">export let</span> size  = <span class="nu">24</span>;
  <span class="kw">export let</span> color = <span class="st">'currentColor'</span>;

  <span class="kw">const</span> CDN   = <span class="st">'{{ baseCdnUrl }}'</span>;
  <span class="kw">const</span> cache = {};
  <span class="kw">let</span>   svg   = <span class="st">''</span>;

  <span class="fn">$</span>: name, <span class="fn">load</span>();

  <span class="kw">async function</span> <span class="fn">load</span>() {
    <span class="kw">if</span> (!name) <span class="kw">return</span>;
    <span class="kw">if</span> (cache[name]) { svg = cache[name]; <span class="kw">return</span>; }
    svg = cache[name] = <span class="kw">await</span> <span class="fn">fetch</span>(<span class="st">`${CDN}?icon=${name}&size=${size}`</span>)
      .<span class="fn">then</span>(r =&gt; r.<span class="fn">text</span>());
  }
&lt;/<span class="kw">script</span>&gt;

{#if svg}
  &lt;<span class="kw">span</span> style=<span class="st">"color:{color};display:inline-flex;align-items:center"</span>
        &gt;{<span class="fn">@html</span> svg}&lt;/<span class="kw">span</span>&gt;
{/if}</code></pre>
                    </div>
                </div>
            </div>

            <div class="cdn-tab-content" data-cdncontent="next">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">Use <strong>'use client'</strong> since the component fetches on the browser. TypeScript-ready.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge next">Next.js 13+</span><span class="fw-badge react">App Router</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">components/MdIcon.tsx</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">tsx</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="st">'use client'</span>;
<span class="kw">import</span> { useState, useEffect } <span class="kw">from</span> <span class="st">'react'</span>;

<span class="kw">const</span> CDN: string = <span class="st">'{{ baseCdnUrl }}'</span>;
<span class="kw">const</span> cache: Record&lt;string, string&gt; = {};

<span class="kw">interface</span> Props { name: string; size?: number; color?: string; className?: string; }

<span class="kw">export default function</span> <span class="fn">MdIcon</span>({ name, size = <span class="nu">24</span>, color = <span class="st">'currentColor'</span>, className = <span class="st">''</span> }: Props) {
  <span class="kw">const</span> [svg, setSvg] = useState&lt;string&gt;(<span class="st">''</span>);

  <span class="fn">useEffect</span>(() =&gt; {
    <span class="kw">if</span> (!name) <span class="kw">return</span>;
    <span class="kw">if</span> (cache[name]) { setSvg(cache[name]); <span class="kw">return</span>; }
    <span class="fn">fetch</span>(<span class="st">`${CDN}?icon=${encodeURIComponent(name)}&size=${size}`</span>)
      .<span class="fn">then</span>(r =&gt; r.<span class="fn">text</span>())
      .<span class="fn">then</span>(s =&gt; { cache[name] = s; setSvg(s); });
  }, [name, size]);

  <span class="kw">if</span> (!svg) <span class="kw">return</span> <span class="kw">null</span>;
  <span class="kw">return</span> (
    &lt;<span class="kw">span</span>
      className={className}
      style={{ color, display: <span class="st">'inline-flex'</span>, alignItems: <span class="st">'center'</span> }}
      dangerouslySetInnerHTML={{ __html: svg }}
    /&gt;
  );
}</code></pre>
                    </div>
                </div>
            </div>

            <div class="cdn-tab-content" data-cdncontent="nuxt">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">Auto-imported composable — fetch SVG icons directly in any Nuxt 3 component.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge nuxt">Nuxt 3</span><span class="fw-badge vue">Vue 3</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">composables/useMdIcon.ts</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">ts</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="kw">const</span> CDN   = <span class="st">'{{ baseCdnUrl }}'</span>;
<span class="kw">const</span> cache: Record&lt;string, string&gt; = {};

<span class="kw">export function</span> <span class="fn">useMdIcon</span>(name: string, size = <span class="nu">24</span>) {
  <span class="kw">const</span> svg = <span class="fn">ref</span>(<span class="st">''</span>);
  <span class="fn">watchEffect</span>(<span class="kw">async</span> () =&gt; {
    <span class="kw">if</span> (!name) <span class="kw">return</span>;
    <span class="kw">if</span> (cache[name]) { svg.value = cache[name]; <span class="kw">return</span>; }
    svg.value = cache[name] = <span class="kw">await</span> <span class="fn">fetch</span>(<span class="st">`${CDN}?icon=${name}&size=${size}`</span>)
      .<span class="fn">then</span>(r =&gt; r.<span class="fn">text</span>());
  });
  <span class="kw">return</span> svg;
}</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">components/MdIcon.vue</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">vue</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>&lt;<span class="kw">script setup</span>&gt;
<span class="kw">const</span> props = <span class="fn">defineProps</span>({ name: String, size: { default: <span class="nu">24</span> }, color: { default: <span class="st">'currentColor'</span> } });
<span class="kw">const</span> svg = <span class="fn">useMdIcon</span>(props.name, props.size);
&lt;/<span class="kw">script</span>&gt;

&lt;<span class="kw">template</span>&gt;
  &lt;<span class="kw">span</span> :<span class="at">style</span>=<span class="st">"`color:${color};display:inline-flex`"</span> v-html=<span class="st">"svg"</span> /&gt;
&lt;/<span class="kw">template</span>&gt;</code></pre>
                    </div>
                </div>
            </div>

            <div class="cdn-tab-content" data-cdncontent="api">
                <div class="cdn-note">
                    <span class="cdn-note-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></span>
                    <span class="cdn-note-text">The CDN serves each icon individually as SVG — bulk JSON is <strong>never exposed</strong> to protect the icon library.</span>
                </div>
                <div class="fw-badges"><span class="fw-badge cdn">REST API</span><span class="fw-badge html">SVG Response</span></div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Loader script (head tag)</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">url</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>GET {{ baseCdnUrl }}
<span class="cm">→ Returns auto-render JavaScript (put in &lt;head&gt; defer)</span></code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Single icon endpoint</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">url</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code>GET {{ baseCdnUrl }}?icon=<span class="st">{name}</span>&size=<span class="nu">24</span>&color=<span class="st">%23ffffff</span>
<span class="cm">→ Returns SVG image (Content-Type: image/svg+xml)</span>
<span class="cm">→ Cached 24h by browser / CDN layer</span>

<span class="cm">Parameters:</span>
  icon   — icon name (required, alphanumeric + dash only)
  size   — px size  (optional, default 24, max 2048)
  color  — hex fill  (optional, default currentColor)</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">HTML attributes</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">html</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="cm">&lt;!-- All supported attributes --&gt;</span>
&lt;<span class="kw">i</span>
  <span class="at">data-icon</span>=<span class="st">"icon-name"</span>    <span class="cm">&lt;!-- required: icon name --&gt;</span>
  <span class="at">data-size</span>=<span class="st">"24"</span>          <span class="cm">&lt;!-- optional: px size (default 24) --&gt;</span>
  <span class="at">data-color</span>=<span class="st">"#4db8ff"</span>    <span class="cm">&lt;!-- optional: fill color --&gt;</span>
  <span class="at">style</span>=<span class="st">"color:#4db8ff"</span>   <span class="cm">&lt;!-- CSS color also works --&gt;</span>
  <span class="at">class</span>=<span class="st">"my-icon"</span>         <span class="cm">&lt;!-- class is preserved --&gt;</span>
&gt;&lt;/<span class="kw">i</span>&gt;</code></pre>
                    </div>
                </div>

                <div class="cdn-section">
                    <div class="cdn-section-label">Security model</div>
                    <div class="cdn-code-block">
                        <span class="cdn-code-lang">text</span>
                        <button class="cdn-code-copy" onclick="copyBlock(this)">Copy</button>
                        <pre><code><span class="cm">✓  Per-icon serving  — no bulk JSON dump endpoint</span>
<span class="cm">✓  CORS origin check — only allowed domains served</span>
<span class="cm">✓  Rate limiting     — 300 req/min per IP</span>
<span class="cm">✓  Name sanitisation — only [a-z0-9-] accepted</span>
<span class="cm">✓  SVG output only   — not raw JSON data</span>
<span class="cm">✓  Cache headers     — 24h browser cache reduces load</span></code></pre>
                    </div>
                </div>
            </div>

        </div></div></div><script>
var ICON_W = {{ globalWidth }};
var ICON_H = {{ globalHeight }};
var CATEGORIES = {{ catJSEncoded|safe }};

var globalColor = '#c8d6e8';
var modalColor  = '#c8d6e8';
var currentModal = null;
var styleFilter  = '';
var categoryFilter = 'all';
var bucket = {};
var globalHsvState = { h: 210, s: 0.15, v: 0.91 };
var modalHsvState  = { h: 210, s: 0.15, v: 0.91 };
var globalPicker, modalPicker;

function hsvToHex(h, s, v) {
    var r, g, b;
    var i = Math.floor(h / 60) % 6;
    var f = h / 60 - Math.floor(h / 60);
    var p = v * (1 - s), q = v * (1 - f * s), t = v * (1 - (1 - f) * s);
    if (i===0){r=v;g=t;b=p;} else if (i===1){r=q;g=v;b=p;} else if (i===2){r=p;g=v;b=t;}
    else if (i===3){r=p;g=q;b=v;} else if (i===4){r=t;g=p;b=v;} else {r=v;g=p;b=q;}
    return '#' + [r,g,b].map(function(x){ return Math.round(x*255).toString(16).padStart(2,'0'); }).join('');
}

function hexToHsv(hex) {
    if (!hex || hex.length < 7) return { h:0, s:0, v:1 };
    var r=parseInt(hex.slice(1,3),16)/255, g=parseInt(hex.slice(3,5),16)/255, b=parseInt(hex.slice(5,7),16)/255;
    var mx=Math.max(r,g,b), mn=Math.min(r,g,b), d=mx-mn, h=0, s=mx===0?0:d/mx, v=mx;
    if (d!==0) {
        if (mx===r) h=((g-b)/d+(g<b?6:0))*60;
        else if (mx===g) h=((b-r)/d+2)*60;
        else h=((r-g)/d+4)*60;
    }
    return { h:h, s:s, v:v };
}

function isValidHex(h) { return /^#[0-9A-Fa-f]{6}$/.test(h); }

function drawHsvCanvas(canvasId, hue) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var wrap = canvas.parentElement;
    var w = wrap.getBoundingClientRect().width || 240;
    var h = wrap.getBoundingClientRect().height || Math.round(w * 0.6);
    if (w < 2) { w = 240; h = 144; }
    canvas.width = w; canvas.height = h;
    var ctx = canvas.getContext('2d');
    var gH = ctx.createLinearGradient(0,0,w,0);
    gH.addColorStop(0, '#fff');
    gH.addColorStop(1, 'hsl(' + hue + ',100%,50%)');
    ctx.fillStyle = gH; ctx.fillRect(0,0,w,h);
    var gV = ctx.createLinearGradient(0,0,0,h);
    gV.addColorStop(0, 'rgba(0,0,0,0)');
    gV.addColorStop(1, '#000');
    ctx.fillStyle = gV; ctx.fillRect(0,0,w,h);
}

function setupHsvPicker(wrapId, canvasId, cursorId, hueBarId, hueThumbId, hexInputId, hexPreviewId, state, onColorChange) {
    var wrap   = document.getElementById(wrapId);
    var hueBar = document.getElementById(hueBarId);

    function redraw() { drawHsvCanvas(canvasId, state.h); }

    function applyColor() {
        var hex = hsvToHex(state.h, state.s, state.v);
        var cursor = document.getElementById(cursorId);
        var thumb  = document.getElementById(hueThumbId);
        var hexIn  = document.getElementById(hexInputId);
        var prev   = document.getElementById(hexPreviewId);
        if (cursor) { cursor.style.left = (state.s * 100) + '%'; cursor.style.top = ((1 - state.v) * 100) + '%'; }
        if (thumb)  { thumb.style.left = (state.h / 360 * 100) + '%'; }
        if (hexIn)  { hexIn.value = hex; }
        if (prev)   { prev.style.background = hex; }
        onColorChange(hex);
    }

    function getSV(e) {
        var rc = wrap.getBoundingClientRect();
        var cx = e.touches ? e.touches[0].clientX : e.clientX;
        var cy = e.touches ? e.touches[0].clientY : e.clientY;
        return { s: Math.max(0,Math.min(1,(cx-rc.left)/rc.width)), v: 1-Math.max(0,Math.min(1,(cy-rc.top)/rc.height)) };
    }

    function getH(e) {
        var rc = hueBar.getBoundingClientRect();
        var cx = e.touches ? e.touches[0].clientX : e.clientX;
        return Math.max(0, Math.min(1, (cx - rc.left) / rc.width)) * 360;
    }

    var dragSV = false, dragH = false;

    wrap.addEventListener('mousedown', function(e) { e.preventDefault(); dragSV=true; var sv=getSV(e); state.s=sv.s; state.v=sv.v; applyColor(); });
    wrap.addEventListener('touchstart', function(e) { e.preventDefault(); dragSV=true; var sv=getSV(e); state.s=sv.s; state.v=sv.v; applyColor(); }, {passive:false});
    hueBar.addEventListener('mousedown', function(e) { e.preventDefault(); dragH=true; state.h=getH(e); redraw(); applyColor(); });
    hueBar.addEventListener('touchstart', function(e) { e.preventDefault(); dragH=true; state.h=getH(e); redraw(); applyColor(); }, {passive:false});

    document.addEventListener('mousemove', function(e) {
        if (dragSV) { var sv=getSV(e); state.s=sv.s; state.v=sv.v; applyColor(); }
        if (dragH)  { state.h=getH(e); redraw(); applyColor(); }
    });
    document.addEventListener('touchmove', function(e) {
        if (dragSV) { e.preventDefault(); var sv=getSV(e); state.s=sv.s; state.v=sv.v; applyColor(); }
        if (dragH)  { e.preventDefault(); state.h=getH(e); redraw(); applyColor(); }
    }, {passive:false});
    document.addEventListener('mouseup',  function() { dragSV=false; dragH=false; });
    document.addEventListener('touchend', function() { dragSV=false; dragH=false; });

    document.getElementById(hexInputId).addEventListener('input', function() {
        var v = this.value.trim();
        if (!v.startsWith('#')) v = '#' + v;
        if (isValidHex(v)) { var hsv=hexToHsv(v); state.h=hsv.h; state.s=hsv.s; state.v=hsv.v; redraw(); applyColor(); }
    });

    redraw();
    applyColor();
    return { redraw: redraw, applyColor: applyColor };
}

function setupCustomSelect(triggerId, dropdownId, labelId, onSelect) {
    var trigger  = document.getElementById(triggerId);
    var dropdown = document.getElementById(dropdownId);
    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        var isOpen = dropdown.classList.contains('open');
        closeAllDropdowns();
        if (!isOpen) { dropdown.classList.add('open'); trigger.classList.add('open'); }
    });
    dropdown.querySelectorAll('.custom-select-option').forEach(function(opt) {
        opt.addEventListener('click', function(e) {
            e.stopPropagation();
            var val = this.getAttribute('data-value');
            document.getElementById(labelId).textContent = this.textContent;
            dropdown.querySelectorAll('.custom-select-option').forEach(function(o){ o.classList.remove('selected'); });
            this.classList.add('selected');
            dropdown.classList.remove('open');
            trigger.classList.remove('open');
            onSelect(val);
        });
    });
}

function closeAllDropdowns() {
    document.querySelectorAll('.custom-select-dropdown').forEach(function(d){ d.classList.remove('open'); });
    document.querySelectorAll('.custom-select-trigger').forEach(function(t){ t.classList.remove('open'); });
    document.querySelectorAll('.color-panel').forEach(function(p){ p.classList.remove('open'); });
}
document.addEventListener('click', function() { closeAllDropdowns(); });

function updateSliderFill(slider) {
    var mn=parseFloat(slider.min), mx=parseFloat(slider.max), v=parseFloat(slider.value);
    slider.style.setProperty('--pct', ((v-mn)/(mx-mn)*100).toFixed(1)+'%');
}

function init() {
    var sc = localStorage.getItem('iconlib_color');
    if (sc && isValidHex(sc)) {
        globalColor = sc;
        var hsv = hexToHsv(sc);
        globalHsvState.h = hsv.h; globalHsvState.s = hsv.s; globalHsvState.v = hsv.v;
    }
    document.documentElement.style.setProperty('--icon-color', globalColor);
    document.getElementById('globalColorPreview').style.background = globalColor;

    var sb = localStorage.getItem('iconlib_bucket');
    if (sb) { try { bucket = JSON.parse(sb); } catch(e) { bucket = {}; } }

    globalPicker = setupHsvPicker('globalHsvWrap','globalHsvCanvas','globalHsvCursor','globalHueBar','globalHueThumb','globalHexInput','globalHexPreviewDot', globalHsvState, function(hex) {
        globalColor = hex;
        document.getElementById('globalColorPreview').style.background = hex;
        document.documentElement.style.setProperty('--icon-color', hex);
        localStorage.setItem('iconlib_color', hex);
    });

    modalPicker = setupHsvPicker('modalHsvWrap','modalHsvCanvas','modalHsvCursor','modalHueBar','modalHueThumb','modalHexInput','modalHexPreviewDot', modalHsvState, function(hex) {
        modalColor = hex;
        var w = document.getElementById('modalIconWrap');
        if (w) { var svg = w.querySelector('svg'); if (svg) svg.style.color = hex; }
    });

    document.getElementById('globalColorTrigger').addEventListener('click', function(e) {
        e.stopPropagation();
        var panel = document.getElementById('globalColorPanel');
        var isOpen = panel.classList.contains('open');
        closeAllDropdowns();
        if (!isOpen) {
            panel.classList.add('open');
            requestAnimationFrame(function() { if (globalPicker) { globalPicker.redraw(); globalPicker.applyColor(); } });
        }
    });

    setupCustomSelect('styleFilterTrigger','styleFilterDropdown','styleFilterLabel', function(val) {
        styleFilter = val; filterIcons();
    });

    document.getElementById('catBar').addEventListener('click', function(e) {
        var chip = e.target.closest('.cat-chip');
        if (!chip) return;
        document.querySelectorAll('.cat-chip').forEach(function(c){ c.classList.remove('active'); });
        chip.classList.add('active');
        categoryFilter = chip.getAttribute('data-cat');
        filterIcons();
    });

    document.getElementById('searchInput').addEventListener('input', filterIcons);

    var slider = document.getElementById('modalSizeSlider');
    slider.addEventListener('input', function() {
        document.getElementById('sizeDisplay').textContent = this.value + 'px';
        updateSliderFill(this);
    });
    updateSliderFill(slider);

    renderBucket(); updateBucketCount(); markFavButtons();

    var pos = localStorage.getItem('iconlib_scroll');
    if (pos) setTimeout(function(){ window.scrollTo(0, parseInt(pos)); }, 80);
    window.addEventListener('scroll', function(){ localStorage.setItem('iconlib_scroll', window.scrollY); }, {passive:true});
}

function filterIcons() {
    var search = document.getElementById('searchInput').value.toLowerCase().trim();
    var cards  = document.querySelectorAll('.icon-card');
    var visible = 0;
    var kws = categoryFilter !== 'all' ? (CATEGORIES[categoryFilter] || []) : [];
    cards.forEach(function(card) {
        var name = card.getAttribute('data-name').toLowerCase();
        var styleOk  = !styleFilter  || name.indexOf(styleFilter)  !== -1;
        var searchOk = !search       || name.indexOf(search)        !== -1;
        var catOk    = categoryFilter === 'all' || (kws.length > 0 && kws.some(function(k){ return name.indexOf(k) !== -1; }));
        if (styleOk && searchOk && catOk) { card.style.display = ''; visible++; }
        else { card.style.display = 'none'; }
    });
    document.getElementById('visibleCount').textContent = visible;
    var nd = document.querySelector('.no-results-dynamic');
    if (visible === 0 && cards.length > 0) {
        if (!nd) {
            var div = document.createElement('div');
            div.className = 'no-results no-results-dynamic';
            div.style.gridColumn = '1/-1';
            div.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><p>No icons found</p>';
            document.getElementById('iconGrid').appendChild(div);
        }
    } else if (nd) { nd.remove(); }
}

function handleCardClick(e, card) {
    if (e.target.closest('.icon-card-fav')) return;
    openModal(card.getAttribute('data-name'), card.getAttribute('data-body'));
}

function openModal(name, body) {
    modalColor = globalColor;
    var hsv = hexToHsv(globalColor);
    modalHsvState.h = hsv.h; modalHsvState.s = hsv.s; modalHsvState.v = hsv.v;
    currentModal = { name: name, body: body };
    document.getElementById('modalIconWrap').innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="66" height="66" viewBox="0 0 '+ICON_W+' '+ICON_H+'" style="color:'+modalColor+';fill:currentColor">'+body+'</svg>';
    document.getElementById('modalIconName').textContent = name;
    
    document.getElementById('modalIconCdnCode').textContent = '<i data-icon="' + name + '"></i>';
    
    document.getElementById('modalHexInput').value = modalColor;
    document.getElementById('modalHexPreviewDot').style.background = modalColor;
    var sl = document.getElementById('modalSizeSlider');
    document.getElementById('sizeDisplay').textContent = sl.value + 'px';
    document.getElementById('modalOverlay').classList.add('open');
    document.body.style.overflow = 'hidden';
    setTimeout(function() { if (modalPicker) { modalPicker.redraw(); modalPicker.applyColor(); } }, 30);
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
    document.body.style.overflow = '';
    currentModal = null;
    closeAllDropdowns();
}

function handleModalOverlayClick(e) {
    if (e.target === document.getElementById('modalOverlay')) closeModal();
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') { closeModal(); closeSidebar(); closeCdnModal(); }
});

function getExportSize() { return parseInt(document.getElementById('modalSizeSlider').value) || 512; }

function getModalSVGString(size) {
    if (!currentModal) return '';
    var s = size || getExportSize();
    return '<svg xmlns="http://www.w3.org/2000/svg" width="'+s+'" height="'+s+'" viewBox="0 0 '+ICON_W+' '+ICON_H+'" style="color:'+modalColor+';fill:currentColor">'+currentModal.body+'</svg>';
}

function downloadSVG() {
    if (!currentModal) return;
    var blob = new Blob([getModalSVGString()], {type:'image/svg+xml'});
    var url  = URL.createObjectURL(blob);
    var a = document.createElement('a'); a.href = url; a.download = currentModal.name + '.svg'; a.click();
    URL.revokeObjectURL(url);
    showToast('SVG downloaded!', 'success');
}

function svgToPNG(size, callback) {
    if (!currentModal) return;
    var svgStr = getModalSVGString(size);
    var img = new Image();
    var canvas = document.getElementById('pngCanvas');
    canvas.width = size; canvas.height = size;
    var ctx = canvas.getContext('2d');
    img.onload = function() { ctx.clearRect(0,0,size,size); ctx.drawImage(img,0,0,size,size); callback(canvas); URL.revokeObjectURL(img.src); };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
}

function downloadPNG() {
    if (!currentModal) return;
    svgToPNG(getExportSize(), function(canvas) {
        var a = document.createElement('a'); a.href = canvas.toDataURL('image/png'); a.download = currentModal.name + '.png'; a.click();
        showToast('PNG downloaded!', 'success');
    });
}

function copySVG() {
    if (!currentModal) return;
    navigator.clipboard.writeText(getModalSVGString(24)).then(function() { showToast('SVG copied!', 'info'); });
}

function copyPNG() {
    if (!currentModal) return;
    svgToPNG(getExportSize(), function(canvas) {
        canvas.toBlob(function(blob) {
            try {
                navigator.clipboard.write([new ClipboardItem({'image/png': blob})]).then(function() { showToast('PNG copied!', 'info'); });
            } catch(e) { showToast('Copy not supported', 'warn'); }
        });
    });
}

function copyIconCDNCode() {
    if (!currentModal) return;
    var tag = '<i data-icon="' + currentModal.name + '"></i>';
    navigator.clipboard.writeText(tag).then(function() { showToast('Tag copied!', 'success'); });
}

function toggleFav(e, btn) {
    e.stopPropagation();
    var name = btn.getAttribute('data-name');
    var card = btn.closest('.icon-card');
    var body = card.getAttribute('data-body');
    if (bucket[name]) {
        delete bucket[name]; btn.classList.remove('active'); showToast('Removed from bucket', 'warn');
    } else {
        bucket[name] = body; btn.classList.add('active'); showToast('Added to bucket!', 'success');
    }
    saveBucket(); updateBucketCount(); renderBucket();
}

function saveBucket() { localStorage.setItem('iconlib_bucket', JSON.stringify(bucket)); }

function updateBucketCount() {
    var count = Object.keys(bucket).length;
    var el = document.getElementById('bucketCount');
    el.textContent = count; el.classList.toggle('visible', count > 0);
    document.getElementById('sidebarBadge').textContent = count;
}

function markFavButtons() {
    document.querySelectorAll('.icon-card-fav').forEach(function(btn) {
        btn.classList.toggle('active', !!bucket[btn.getAttribute('data-name')]);
    });
}

function renderBucket() {
    var body = document.getElementById('sidebarBody');
    var keys = Object.keys(bucket);
    if (keys.length === 0) {
        body.innerHTML = '<div class="sidebar-empty"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg><p>Bucket is empty.<br>Tap the heart on any icon.</p></div>';
        return;
    }
    var list = document.createElement('div');
    list.className = 'bucket-list';
    keys.forEach(function(name) {
        var svgBody = bucket[name];
        var item = document.createElement('div');
        item.className = 'bucket-item';
        item.innerHTML = '<div class="bucket-item-icon"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 '+ICON_W+' '+ICON_H+'" style="fill:currentColor;color:'+globalColor+'">'+svgBody+'</svg></div><div class="bucket-item-name">'+escapeHtml(name)+'</div><button class="bucket-item-remove" title="Remove"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';
        item.querySelector('.bucket-item-remove').addEventListener('click', function(e) { e.stopPropagation(); removeFromBucket(name); });
        item.addEventListener('click', function() { openModal(name, svgBody); closeSidebar(); });
        list.appendChild(item);
    });
    body.innerHTML = '';
    body.appendChild(list);
}

function removeFromBucket(name) {
    delete bucket[name]; saveBucket(); updateBucketCount(); renderBucket();
    var btn = document.querySelector('.icon-card-fav[data-name="'+CSS.escape(name)+'"]');
    if (btn) btn.classList.remove('active');
    showToast('Removed from bucket', 'warn');
}

function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

document.getElementById('bucketBtn').addEventListener('click', function() {
    document.getElementById('sidebar').classList.add('open');
    document.getElementById('sidebarOverlay').classList.add('open');
    document.body.style.overflow = 'hidden';
});

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('open');
    document.body.style.overflow = '';
}

function showToast(msg, type) {
    var container = document.getElementById('toastContainer');
    var toast = document.createElement('div');
    toast.className = 'toast';
    var dc = type === 'warn' ? 'warn' : type === 'info' ? 'info' : '';
    toast.innerHTML = '<div class="toast-dot ' + dc + '"></div>' + escapeHtml(msg);
    container.appendChild(toast);
    setTimeout(function() { toast.classList.add('hiding'); setTimeout(function(){ toast.remove(); }, 220); }, 2200);
}

/* ════════════════════════════
   CDN MODAL LOGIC
════════════════════════════ */
var CDN_SCRIPT = '<script src="{{ baseCdnUrl }}" defer><\/script>';
var CDN_ICON   = '{{ baseCdnUrl }}';

function openCdnModal() {
    document.getElementById('cdnModalOverlay').classList.add('open');
    document.body.style.overflow = 'hidden';
}
function closeCdnModal() {
    document.getElementById('cdnModalOverlay').classList.remove('open');
    document.body.style.overflow = '';
}
function handleCdnOverlayClick(e) {
    if (e.target === document.getElementById('cdnModalOverlay')) closeCdnModal();
}

/* CDN big modal tab switching */
document.querySelectorAll('.cdn-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
        var key = this.getAttribute('data-cdntab');
        document.querySelectorAll('.cdn-tab').forEach(function(t){ t.classList.remove('active'); });
        document.querySelectorAll('.cdn-tab-content').forEach(function(c){ c.classList.remove('active'); });
        this.classList.add('active');
        document.querySelector('[data-cdncontent="'+key+'"]').classList.add('active');
    });
});

/* Copy CDN script tag */
function copyCdnUrl() {
    navigator.clipboard.writeText(CDN_SCRIPT).then(function(){
        showToast('Script tag copied!', 'info');
    });
}

function copyMainCDN() {
    var cdnTag = document.getElementById('mainCdnScript').innerText;
    navigator.clipboard.writeText(cdnTag).then(function() { showToast('CDN script copied!', 'success'); });
}

/* Copy code block — grabs pre innerText (strips HTML spans) */
function copyBlock(btn) {
    var pre = btn.closest('.cdn-code-block').querySelector('pre');
    var text = pre.innerText || pre.textContent;
    navigator.clipboard.writeText(text).then(function(){
        var orig = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(function(){ btn.textContent = orig; }, 1600);
    });
}

/* Mini copy inside icon modal */
function miniCopy(id) {
    var el = document.getElementById(id);
    navigator.clipboard.writeText(el.innerText || el.textContent).then(function(){
        showToast('Code copied!', 'info');
    });
}

/* Toggle CDN accordion inside icon modal */
function toggleModalCdn(header) {
    var body    = document.getElementById('modalCdnBody');
    var chevron = header.querySelector('.modal-cdn-chevron');
    var isOpen  = body.classList.contains('open');
    body.classList.toggle('open', !isOpen);
    chevron.classList.toggle('open', !isOpen);
}

/* Mini tabs inside icon modal */
document.addEventListener('click', function(e) {
    var t = e.target.closest('.mini-tab');
    if (!t) return;
    var bar    = t.closest('.mini-tabs');
    var parent = bar.parentElement;
    bar.querySelectorAll('.mini-tab').forEach(function(x){ x.classList.remove('active'); });
    t.classList.add('active');
    var key = t.getAttribute('data-minitab');
    parent.querySelectorAll('.mini-code-panel').forEach(function(p){ p.classList.remove('active'); });
    var target = document.getElementById('mini' + key.charAt(0).toUpperCase() + key.slice(1));
    if (target) target.classList.add('active');
});

/* Fill mini code panels when an icon modal opens */
function fillMiniCdnCodes(iconName) {
    var cdnUrl = CDN_ICON;

    var htmlCode =
        '\\n' +
        '<script src="' + cdnUrl + '" defer><\\/script>\\n\\n' +
        '\\n' +
        '<i data-icon="' + iconName + '" data-size="24"></i>';

    var reactCode =
        'import MdIcon from \\'./components/MdIcon\\';\\n\\n' +
        '// Fetches from: ' + cdnUrl + '?icon=' + iconName + '\\n' +
        '<MdIcon name="' + iconName + '" size={24} color="currentColor" />';

    var vueCode =
        '\\n' +
        '<MdIcon name="' + iconName + '" :size="24" color="currentColor" />';

    var svelteCode =
        '\\n' +
        '<MdIcon name="' + iconName + '" size={24} color="currentColor" />';

    var nextCode =
        'import MdIcon from \\'@/components/MdIcon\\';\\n\\n' +
        '// Fetches: ' + cdnUrl + '?icon=' + iconName + '\\n' +
        '<MdIcon name="' + iconName + '" size={24} color="currentColor" />';

    var set = function(id, val) {
        var el = document.getElementById(id);
        if (el) el.textContent = val;
    };
    set('miniHtmlCode',   htmlCode);
    set('miniReactCode',  reactCode);
    set('miniVueCode',    vueCode);
    set('miniSvelteCode', svelteCode);
    set('miniNextCode',   nextCode);
}

var _origOpenModal = openModal;
openModal = function(name, body) {
    _origOpenModal(name, body);
    fillMiniCdnCodes(name);
    
    var cdnBody = document.getElementById('modalCdnBody');
    if (cdnBody) cdnBody.classList.remove('open');
    var chevron = document.querySelector('.modal-cdn-chevron');
    if (chevron) chevron.classList.remove('open');
    
    document.querySelectorAll('.mini-tab').forEach(function(t, i){ t.classList.toggle('active', i === 0); });
    document.querySelectorAll('.mini-code-panel').forEach(function(p, i){ p.classList.toggle('active', i === 0); });
};

init();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)
