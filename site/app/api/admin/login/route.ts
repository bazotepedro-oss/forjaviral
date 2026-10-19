// POST /api/admin/login
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { createAdminSession, setAdminCookieHeader } from '@/lib/auth';

const Schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const parsed = Schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Credenciais inválidas' }, { status: 400 });
  }
  const token = await createAdminSession(parsed.data.email, parsed.data.password);
  if (!token) {
    return NextResponse.json({ error: 'Credenciais inválidas' }, { status: 401 });
  }
  return NextResponse.json(
    { ok: true },
    { headers: { 'Set-Cookie': setAdminCookieHeader(token) } }
  );
}