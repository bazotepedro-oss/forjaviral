import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { prisma } from '@/lib/db';

export async function POST(req: Request) {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  const { customerId } = await req.json().catch(() => ({}));
  if (!customerId) return NextResponse.json({ error: 'ID do cliente obrigatório' }, { status: 400 });

  try {
    await prisma.accessCredentials.deleteMany({ where: { customerId } });
    await prisma.subscription.deleteMany({ where: { customerId } });
    await prisma.order.deleteMany({ where: { customerId } });
    await prisma.customer.delete({ where: { id: customerId } });

    return NextResponse.json({ ok: true, message: 'Cliente removido do CRM com sucesso' });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || 'Erro ao remover cliente' }, { status: 500 });
  }
}
