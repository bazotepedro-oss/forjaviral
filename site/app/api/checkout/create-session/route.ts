// POST /api/checkout/create-session
// Body: { slug, name, email, phone?, consent }
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/db';
import { rateLimit } from '@/lib/ratelimit';
import { getPlanId, createCheckout } from '@/lib/abacatepay';
import { generateId, parsePlanIds } from '@/lib/utils';

const Schema = z.object({
  slug: z.string().min(1, 'Plano obrigatório'),
  name: z.string().min(2, 'Nome muito curto').max(120),
  email: z.string().email('E-mail inválido'),
  phone: z.string().max(30).optional(),
  consent: z.literal(true, { message: 'Você precisa aceitar os termos' }),
});

export async function POST(req: Request) {
  // Rate limit by IP
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown';
  const rl = rateLimit(`checkout:${ip}`);
  if (!rl.ok) {
    return NextResponse.json(
      { error: 'Muitas tentativas. Tente novamente em instantes.' },
      { status: 429 }
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'JSON inválido' }, { status: 400 });
  }

  const parsed = Schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Dados inválidos', details: parsed.error.flatten() },
      { status: 400 }
    );
  }
  const { slug, name, email, phone } = parsed.data;

  const plan = await prisma.plan.findUnique({ where: { slug } });
  if (!plan || !plan.active) {
    return NextResponse.json({ error: 'Plano indisponível' }, { status: 404 });
  }

  // Upsert customer
  let customer = await prisma.customer.findUnique({ where: { email } });
  if (!customer) {
    customer = await prisma.customer.create({ data: { name, email, phone } });
  } else {
    customer = await prisma.customer.update({
      where: { id: customer.id },
      data: { name, email, phone: phone ?? customer.phone },
    });
  }

  // Create order
  const order = await prisma.order.create({
    data: {
      customerId: customer.id,
      planId: plan.id,
      status: 'pending',
      amount: plan.price,
      currency: plan.currency,
      metadata: { slug, source: 'site' },
    },
  });


  // AbacatePay plan id
  const abacatePlanId = plan.abacatePlanId || getPlanId(slug);
  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  const returnURL = process.env.ABACATEPAY_RETURN_URL || `${appUrl}/retorno`;

  let checkout;
  try {
    checkout = await createCheckout({
      planSlug: slug,
      planId: abacatePlanId || slug,
      amount: plan.price,
      currency: 'BRL',
      customer: { name, email, phone },
      metadata: { orderId: order.id, slug, email },
      returnURL,
      appName: process.env.ABACATEPAY_APP_NAME || 'Forja Viral',
    });
  } catch (e: any) {
    await prisma.order.update({
      where: { id: order.id },
      data: { status: 'failed', metadata: { ...(order.metadata as any), error: e.message } },
    });
    return NextResponse.json(
      { error: 'Não foi iniciar o checkout. Tente novamente.', detail: e.message },
      { status: 502 }
    );
  }

  // Update order with checkout id
  await prisma.order.update({
    where: { id: order.id },
    data: {
      abacateCheckoutId: checkout.checkoutId,
      abacateOrderId: checkout.orderId,
      metadata: { ...(order.metadata as any), checkoutId: checkout.checkoutId },
    },
  });

  return NextResponse.json({
    ok: true,
    orderId: order.id,
    checkoutURL: checkout.checkoutURL,
  });
}