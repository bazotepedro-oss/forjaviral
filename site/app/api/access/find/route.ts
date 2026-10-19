// GET /api/access/find — busca credenciais ativas do cliente por e-mail ou orderId
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { colabUrl, courseUrl } from '@/lib/provisioning';

export const runtime = 'nodejs';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const email = (searchParams.get('email') || '').trim().toLowerCase();
  const orderId = (searchParams.get('orderId') || '').trim();

  if (!email && !orderId) {
    return NextResponse.json({ error: 'Informe seu e-mail ou o ID do pedido.' }, { status: 400 });
  }

  const whereConditions: any = { status: 'active' };

  if (email) {
    const customer = await prisma.customer.findUnique({ where: { email } });
    if (!customer) {
      return NextResponse.json(
        { error: 'Nenhuma conta encontrada para este e-mail. Se acabou de pagar, aguarde 1 a 2 minutos pela compensação do Pix.' },
        { status: 404 }
      );
    }
    whereConditions.customerId = customer.id;
  }

  if (orderId) {
    whereConditions.orderId = orderId;
  }

  const cred = await prisma.accessCredentials.findFirst({
    where: whereConditions,
    orderBy: { createdAt: 'desc' },
    include: {
      customer: true,
      order: { include: { plan: true } },
    },
  });

  if (!cred) {
    return NextResponse.json(
      { error: 'Acesso ainda não liberado ou pagamento pendente. Aguarde a confirmação do Pix ou entre em contato com o suporte.' },
      { status: 404 }
    );
  }

  return NextResponse.json({
    ok: true,
    username: cred.username,
    licenseKey: cred.licenseKey || 'FV-ATIVADA',
    credits: cred.credits || 100,
    accessUrl: cred.accessUrl,
    courseUrl: cred.courseUrl || courseUrl(),
    colabUrl: colabUrl(),
    planName: cred.order?.plan?.name || 'Forja Viral',
    status: cred.status,
    expiresAt: cred.expiresAt,
  });
}
