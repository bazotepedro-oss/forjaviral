// POST /api/admin/logout
import { NextResponse } from 'next/server';
import { clearAdminCookieHeader } from '@/lib/auth';

export async function POST() {
  return NextResponse.json(
    { ok: true },
    { headers: { 'Set-Cookie': clearAdminCookieHeader() } }
  );
}