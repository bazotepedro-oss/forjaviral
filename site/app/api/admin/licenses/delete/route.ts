import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { deleteLicenseOnServer } from '@/lib/license-server';
import { prisma } from '@/lib/db';

export async function POST(req: Request) {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  const { licenseKey } = await req.json();
  if (!licenseKey) return NextResponse.json({ error: 'Chave obrigatória' }, { status: 400 });

  const res = await deleteLicenseOnServer(licenseKey);

  // Remove ou marca como revogada no banco local
  await prisma.accessCredentials.updateMany({
    where: { licenseKey },
    data: { status: 'revoked', updatedAt: new Date() },
  });

  return NextResponse.json(res);
}
