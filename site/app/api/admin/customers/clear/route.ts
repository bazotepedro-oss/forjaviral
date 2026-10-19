import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { prisma } from '@/lib/db';

export async function POST() {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  try {
    // Remove credenciais, assinaturas, pedidos e clientes
    await prisma.accessCredentials.deleteMany({});
    await prisma.subscription.deleteMany({});
    await prisma.order.deleteMany({});
    await prisma.customer.deleteMany({});

    return NextResponse.json({ ok: true, message: 'CRM limpo com sucesso' });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message || 'Erro ao limpar CRM' }, { status: 500 });
  }
}
