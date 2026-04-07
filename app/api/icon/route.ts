import { NextRequest, NextResponse } from 'next/server';
import { loadIcons } from '@/lib/icons';

const RATE_MAP = new Map<string, { count: number; ts: number }>();
const RATE_LIMIT = 300;

const ALLOWED_ORIGINS = [
  'https://icons.mdjhs.com',
  'https://icons.microstock.store',
];

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

function corsHeaders(origin: string | null): Record<string, string> {
  const allowed =
    !origin ||
    origin.startsWith('http://localhost') ||
    origin.startsWith('http://127.0.0.1') ||
    ALLOWED_ORIGINS.some((o) => origin.startsWith(o));

  return {
    'Access-Control-Allow-Origin': allowed ? (origin ?? '*') : 'null',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Vary': 'Origin',
  };
}

export async function OPTIONS(req: NextRequest) {
  const origin = req.headers.get('origin');
  return new NextResponse(null, { status: 204, headers: corsHeaders(origin) });
}

export async function GET(req: NextRequest) {
  const ip     = req.headers.get('x-forwarded-for')?.split(',')[0].trim() ?? '0.0.0.0';
  const origin = req.headers.get('origin');
  const cors   = corsHeaders(origin);

  if (!rateLimit(ip)) {
    return NextResponse.json({ error: 'Rate limit exceeded' }, { status: 429, headers: cors });
  }

  const { searchParams } = req.nextUrl;
  const rawName  = searchParams.get('name') ?? '';
  const name     = rawName.toLowerCase().replace(/[^a-z0-9-]/g, '');
  const size     = Math.max(8, Math.min(2048, parseInt(searchParams.get('size') ?? '24', 10)));
  const rawColor = searchParams.get('color') ?? '';
  const color    = /^#[0-9a-fA-F]{3,6}$/.test(rawColor) ? rawColor : 'currentColor';

  if (!name) {
    return NextResponse.json({ error: 'name is required' }, { status: 400, headers: cors });
  }

  const data = loadIcons();
  const icon = data.icons[name];

  if (!icon) {
    return NextResponse.json({ error: `Icon not found: ${name}` }, { status: 404, headers: cors });
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${data.width ?? 24} ${data.height ?? 24}" fill="${color}">${icon.body}</svg>`;

  return new NextResponse(svg, {
    headers: {
      ...cors,
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'public, max-age=86400, immutable',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
