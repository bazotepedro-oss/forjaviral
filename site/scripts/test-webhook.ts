import { prisma } from '@/lib/db';

async function main() {
  // Cria um customer de teste e uma order paga, depois simula webhook paid.
  const customer = await prisma.customer.upsert({
    where: { email: 'teste@exemplo.com' },
    update: {},
    create: { name: 'Cliente Teste', email: 'teste@exemplo.com' },
  });
  const plan = await prisma.plan.findUnique({ where: { slug: 'trimestral' } });
  if (!plan) { console.error('Plano trimestral não encontrado. Rode seed.ts primeiro.'); return; }

  const order = await prisma.order.create({
    data: { customerId: customer.id, planId: plan.id, status: 'pending', amount: plan.price, currency: plan.currency },
  });

  // Simula webhook paid
  const { verifyWebhookSignature } = await import('@/lib/abacatepay');
  const payload = JSON.stringify({
    id: 'evt_test_' + Date.now(),
    type: 'checkout.completed',
    data: { status: 'paid', checkoutId: 'chk_test', orderId: 'ord_test', amount: plan.price, metadata: { orderId: order.id } },
  });
  const secret = process.env.ABACATEPAY_WEBHOOK_SECRET || 'test-secret';
  const { signHmac } = await import('@/lib/utils');
  const signature = signHmac(payload, secret);

  const res = await fetch('http://localhost:3000/api/webhooks/abacatepay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-abacatepay-signature': signature },
    body: payload,
  });
  console.log('Webhook status:', res.status, await res.json());

  const creds = await prisma.accessCredentials.findFirst({ where: { orderId: order.id } });
  console.log('Credencial criada:', creds ? { id: creds.id, username: creds.username } : 'NÃO');
}

main().catch((e) => { console.error(e); process.exit(1); }).finally(async () => { await prisma.$disconnect(); });