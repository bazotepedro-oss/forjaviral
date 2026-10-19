import { prisma } from '@/lib/db';

async function main() {
  // Fluxo completo: criar order, simular paid, verificar credencial, testar token expirado.
  const customer = await prisma.customer.upsert({
    where: { email: 'flow@exemplo.com' },
    update: {},
    create: { name: 'Flow Teste', email: 'flow@exemplo.com' },
  });
  const plan = await prisma.plan.findUnique({ where: { slug: 'mensal' } });
  if (!plan) { console.error('Rode seed.ts primeiro.'); return; }

  const order = await prisma.order.create({
    data: { customerId: customer.id, planId: plan.id, status: 'pending', amount: plan.price, currency: plan.currency },
  });

  const { signHmac } = await import('@/lib/utils');
  const payload = JSON.stringify({
    id: 'evt_flow_' + Date.now(),
    type: 'checkout.completed',
    data: { status: 'paid', checkoutId: 'chk_flow', orderId: 'ord_flow', metadata: { orderId: order.id } },
  });
  const secret = process.env.ABACATEPAY_WEBHOOK_SECRET || 'test-secret';
  const signature = signHmac(payload, secret);

  const res = await fetch('http://localhost:3000/api/webhooks/abacatepay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-abacatepay-signature': signature },
    body: payload,
  });
  console.log('Webhook:', res.status, await res.json());

  const updated = await prisma.order.findUnique({ where: { id: order.id } });
  console.log('Order status:', updated?.status);

  const creds = await prisma.accessCredentials.findFirst({ where: { orderId: order.id } });
  console.log('Credencial:', creds ? 'OK' : 'FALHA');

  // Teste de cancelamento
  const cancelPayload = JSON.stringify({
    id: 'evt_cancel_' + Date.now(),
    type: 'subscription.cancelled',
    data: { status: 'canceled', metadata: { orderId: order.id } },
  });
  const cancelSig = signHmac(cancelPayload, secret);
  await fetch('http://localhost:3000/api/webhooks/abacatepay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-abacatepay-signature': cancelSig },
    body: cancelPayload,
  });
  const afterCancel = await prisma.accessCredentials.findFirst({ where: { id: creds?.id } });
  console.log('Após cancelamento, credencial status:', afterCancel?.status);
}

main().catch((e) => { console.error(e); process.exit(1); }).finally(async () => { await prisma.$disconnect(); });