// POST /api/webhooks/abacatepay
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { rateLimit } from '@/lib/ratelimit';
import { verifyWebhookSignature, parseWebhookEvent, mapStatus } from '@/lib/abacatepay';
import { generateId } from '@/lib/utils';
import { provision, revokeCredential } from '@/lib/provisioning';
import { addCreditsOnServer } from '@/lib/license-server';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown';
  const rl = rateLimit(`webhook:${ip}`, { max: 120, windowMs: 60000 });
  if (!rl.ok) return NextResponse.json({ error: 'rate limited' }, { status: 429 });

  const rawPayload = await req.text();
  const signature = req.headers.get('x-abacatepay-signature') || req.headers.get('abacatepay-signature');
  const urlObj = new URL(req.url);
  const querySecret = urlObj.searchParams.get('webhookSecret') || urlObj.searchParams.get('secret');

  if (!verifyWebhookSignature(rawPayload, signature, querySecret)) {
    return NextResponse.json({ error: 'invalid signature' }, { status: 401 });
  }

  let event: any;
  try {
    event = parseWebhookEvent(rawPayload);
  } catch {
    return NextResponse.json({ error: 'invalid payload' }, { status: 400 });
  }

  const eventId = event.id || generateId('evt');

  // Persist raw event for audit
  const created = await prisma.webhookEvent.create({
    data: {
      provider: 'AbacatePay',
      eventId,
      type: event.type,
      payload: event,
      signature: signature || undefined,
      processed: false,
    },
  });

  // Idempotência
  if (created.processed) {
    return NextResponse.json({ ok: true, duplicate: true });
  }

  const status = mapStatus(event.data?.status);
  const checkoutId = event.data?.checkoutId;
  const orderId = event.data?.orderId;
  const metadata = event.data?.metadata || {};
  const internalOrderId = metadata.orderId as string | undefined;

  // Localizar order
  const orConditions: any[] = [];
  if (checkoutId) orConditions.push({ abacateCheckoutId: checkoutId });
  if (internalOrderId) orConditions.push({ id: internalOrderId });
  if (orderId) orConditions.push({ abacateOrderId: orderId });

  const order = orConditions.length
    ? await prisma.order.findFirst({ where: { OR: orConditions } })
    : null;

  if (!order) {
    await prisma.webhookEvent.update({
      where: { id: created.id },
      data: { processed: true, orderId: undefined },
    });
    return NextResponse.json({ ok: true, note: 'order not found' });
  }

  // Atualizar status
  const updateData: any = { status };
  if (status === 'paid') updateData.paidAt = new Date();
  await prisma.order.update({ where: { id: order.id }, data: updateData });

  // Vincular evento à order
  await prisma.webhookEvent.update({
    where: { id: created.id },
    data: { orderId: order.id },
  });

  if (status === 'paid') {
    const meta = (order.metadata as any) || {};
    if (meta.isRecharge && meta.licenseKey && meta.creditsToAdd) {
      try {
        await addCreditsOnServer(meta.licenseKey, Number(meta.creditsToAdd));
        console.log(`[Webhook] Recarga automática de ${meta.creditsToAdd} créditos para a chave ${meta.licenseKey}`);
      } catch (e: any) {
        console.error('[Webhook] Falha na recarga de créditos:', e?.message);
      }
    }

    let subscription = await prisma.subscription.findFirst({
      where: { customerId: order.customerId, planId: order.planId, status: 'active' },
    });
    if (!subscription) {
      subscription = await prisma.subscription.create({
        data: {
          customerId: order.customerId,
          planId: order.planId,
          status: 'active',
          provider: 'AbacatePay',
          providerSubscriptionId: event.data?.subscriptionId,
          orderId: order.id,
        },
      });
    } else if (event.data?.subscriptionId) {
      subscription = await prisma.subscription.update({
        where: { id: subscription.id },
        data: { status: 'active', providerSubscriptionId: event.data.subscriptionId },
      });
    }

    const customer = await prisma.customer.findUnique({ where: { id: order.customerId } });
    const plan = await prisma.plan.findUnique({ where: { id: order.planId } });
    if (customer && plan) {
      try {
        await provision({
          customerId: customer.id,
          orderId: order.id,
          subscriptionId: subscription.id,
          email: customer.email,
          plan: plan.slug,
        });
      } catch (e: any) {
        console.error('provision error:', e.message);
      }
    }
  } else if (status === 'canceled' || status === 'refunded') {
    const creds = await prisma.accessCredentials.findMany({
      where: { orderId: order.id, status: 'active' },
    });
    for (const c of creds) {
      await revokeCredential(c.id, `provider status: ${status}`);
    }
    await prisma.subscription.updateMany({
      where: { customerId: order.customerId, status: 'active' },
      data: { status: status === 'canceled' ? 'canceled' : 'suspended' },
    });
  }

  await prisma.webhookEvent.update({
    where: { id: created.id },
    data: { processed: true },
  });

  return NextResponse.json({ ok: true });
}