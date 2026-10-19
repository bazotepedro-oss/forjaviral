import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { syncAbacatePay } from '@/lib/sync-abacatepay';

export async function POST() {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  const result = await syncAbacatePay();
  return NextResponse.json({ ok: true, ...result });
}
