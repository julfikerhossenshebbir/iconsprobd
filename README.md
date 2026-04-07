# MD Icon Library — Next.js

Professional icon library website — deployable on **Vercel** via GitHub in minutes.

## 🚀 Deploy to Vercel

### One-click
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### Manual
```bash
# 1. Push this repo to GitHub
# 2. Import on vercel.com → New Project → select repo
# 3. Done — no environment variables needed
```

---

## 🛠 Local development

```bash
npm install
npm run dev
# open http://localhost:3000
```

---

## 📦 Add your icons

Replace `public/icons.json` with your own icon set. Format:

```json
{
  "width": 24,
  "height": 24,
  "prefix": "icons",
  "icons": {
    "icon-name": {
      "body": "<path d='...' />"
    }
  }
}
```

The `body` field is the inner SVG content (everything inside `<svg>...</svg>`).

---

## 🔌 CDN Usage (after deploy)

### HTML (Cloudflare-style)
```html
<head>
  <script src="https://YOUR-DOMAIN/api/cdn" defer></script>
</head>
<body>
  <i data-icon="home-smile" data-size="28" style="color:#4db8ff"></i>
  <i data-icon="arrow-right" data-size="20"></i>
</body>
```

### React / Next.js
```tsx
// Fetches: /api/icon?name=home-smile&size=24
<MdIcon name="home-smile" size={24} color="#4db8ff" />
```

---

## 📁 Project structure

```
iconlib/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Server component (reads icons.json)
│   ├── globals.css             # All styles
│   ├── components/
│   │   └── IconLibrary.tsx     # Full client UI
│   └── api/
│       ├── cdn/route.ts        # GET /api/cdn → JS loader script
│       └── icon/route.ts       # GET /api/icon?name=X → SVG
├── lib/
│   └── icons.ts                # Server-side icon loader + categories
├── public/
│   └── icons.json              # ← Replace with your icons
├── package.json
├── next.config.mjs
└── tsconfig.json
```

---

## 🔒 Security

- `/api/icon` serves **one icon at a time** — bulk JSON never exposed
- Rate limit: 300 req/min per IP
- Icon names sanitised to `[a-z0-9-]` only
- 24h browser cache on icon responses

---

## Features

- 🔍 Search + category filter + style filter
- 🎨 Global & per-icon HSV color picker
- 📥 Download SVG / PNG at any size
- 📋 Copy SVG / PNG to clipboard
- 🪣 Bucket (save favourite icons, persists in localStorage)
- 💻 CDN docs modal with React / Vue / Svelte / Next.js / Nuxt examples
- 📱 Fully responsive — mobile → desktop
