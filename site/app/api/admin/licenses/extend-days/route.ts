import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { extendDaysOnServer } from '@/lib/license-server';
import { prisma } from '@/lib/db';

export async function POST(req: Request) {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  const { licenseKey, days } = await req.json();
  const numDays = Number(days) || 30;
  if (!licenseKey) return NextResponse.json({ error: 'Chave obrigatória' }, { status: 400 });

  const res = await extendDaysOnServer(licenseKey, numDays);

  // Atualiza também na base local do site
  const creds = await prisma.accessCredentials.findMany({ where: { licenseKey } });
  for (const c of creds) {
    const currentExp = c.expiresAt ? new Date(c.expiresAt).getTime() : Date.now();
    const newExp = new Date(Math.max(Date.now(), currentExp) + numDays * 86400000);
    await prisma.accessCredentials.update({
      where: { id: c.id },
      data: { expiresAt: newExp, updatedAt: new Date() },
    });
  }

  return NextResponse.json(res);
}
