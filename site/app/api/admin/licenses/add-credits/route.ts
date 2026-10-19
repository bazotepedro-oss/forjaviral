import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { addCreditsOnServer } from '@/lib/license-server';
import { prisma } from '@/lib/db';

export async function POST(req: Request) {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  const { licenseKey, credits } = await req.json();
  const numCredits = Number(credits) || 100;
  if (!licenseKey) return NextResponse.json({ error: 'Chave obrigatória' }, { status: 400 });

  const res = await addCreditsOnServer(licenseKey, numCredits);

  // Atualiza também na base local do site para sincronia visual
  await prisma.accessCredentials.updateMany({
    where: { licenseKey },
    data: {
      credits: { increment: numCredits },
      updatedAt: new Date(),
    },
  });

  return NextResponse.json(res);
}
