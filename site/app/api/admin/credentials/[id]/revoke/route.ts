// POST /api/admin/credentials/[id]/revoke
import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { revokeCredential } from '@/lib/provisioning';

export async function POST(req: Request, { params }: { params: { id: string } }) {
  const admin = await verifyAdminRequest();
  if (!admin) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  await revokeCredential(params.id, 'manual admin');
  return NextResponse.json({ ok: true });
}