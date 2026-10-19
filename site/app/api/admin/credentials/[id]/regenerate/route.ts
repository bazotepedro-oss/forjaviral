// POST /api/admin/credentials/[id]/regenerate
import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { generateToken, hashToken } from '@/lib/utils';

export async function POST(req: Request, { params }: { params: { id: string } }) {
  const admin = await verifyAdminRequest();
  if (!admin) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const token = generateToken(32);
  await prisma.accessCredentials.update({
    where: { id: params.id },
    data: { accessTokenHash: hashToken(token), updatedAt: new Date() },
  });
  await prisma.auditLog.create({
    data: { eventType: 'credential_regenerated', userId: admin.adminId, orderId: undefined, message: `Credential ${params.id} regenerated` },
  });
  return NextResponse.json({ ok: true, token });
}