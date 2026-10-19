// POST /api/checkout/recharge — Cria sessão de recarga de créditos com AbacatePay
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/db';
import { rateLimit } from '@/lib/ratelimit';
import { createCheckout } from '@/lib/abacatepay';

const Schema = z.object({
  licenseKey: z.string().min(5, 'Chave de licença inválida'),
  packageSlug: z.enum(['recarga-100', 'recarga-300', 'recarga-600']),
  name: z.string().min(2, 'Nome muito curto'),
  email: z.string().email('E-mail inválido'),
  phone: z.string().optional(),
});

const RECHARGE_PACKAGES = {
  'recarga-100': { name: 'Recarga 100 Créditos', credits: 100, price: 2990 }, // R$ 29,90
  'recarga-300': { name: 'Recarga 300 Créditos', credits: 300, price: 5990 }, // R$ 59,90
  'recarga-600': { name: 'Recarga 600 Créditos', credits: 600, price: 9990 }, // R$ 99,90
};

export async function POST(req: Request) {
  const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown';
  const rl = rateLimit(`recharge:${ip}`);
  if (!rl.ok) {
    return NextResponse.json({ error: 'Muitas tentativas. Aguarde um instante.' }, { status: 429 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'JSON inválido' }, { status: 400 });
  }

  const parsed = Schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Dados inválidos', details: parsed.error.flatten() }, { status: 400 });
  }

  const { licenseKey, packageSlug, name, email, phone } = parsed.data;
  const pkg = RECHARGE_PACKAGES[packageSlug];

  // 1. Localiza ou cria o cliente
  let customer = await prisma.customer.findUnique({ where: { email } });
  if (!customer) {
    customer = await prisma.customer.create({ data: { name, email, phone } });
  }

  // 2. Garante que o plano de recarga existe no banco local para chave estrangeira
  let plan = await prisma.plan.findUnique({ where: { slug: packageSlug } });
  if (!plan) {
    plan = await prisma.plan.create({
      data: {
        name: pkg.name,
        slug: packageSlug,
        price: pkg.price,
        currency: 'BRL',
        interval: 'one_time',
        features: JSON.stringify([`+${pkg.credits} Créditos automáticos no Forja Viral`]),
        active: true,
      },
    });
  }

  // 3. Cria a ordem de recarga
  const order = await prisma.order.create({
    data: {
      customerId: customer.id,
      planId: plan.id,
      status: 'pending',
      amount: pkg.price,
      currency: 'BRL',
      metadata: {
        isRecharge: true,
        licenseKey,
        creditsToAdd: pkg.credits,
        packageSlug,
      },
    },
  });

  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  const returnURL = `${appUrl}/retorno`;

  try {
    const checkout = await createCheckout({
      planSlug: packageSlug,
      planId: packageSlug,
      amount: pkg.price,
      currency: 'BRL',
      customer: { name, email, phone },
      metadata: {
        orderId: order.id,
        isRecharge: 'true',
        licenseKey,
        creditsToAdd: String(pkg.credits),
      },
      returnURL,
      appName: `Forja Viral - ${pkg.name}`,
    });

    await prisma.order.update({
      where: { id: order.id },
      data: {
        abacateCheckoutId: checkout.checkoutId,
        abacateOrderId: checkout.orderId,
      },
    });

    return NextResponse.json({
      ok: true,
      orderId: order.id,
      checkoutURL: checkout.checkoutURL,
    });
  } catch (err: any) {
    await prisma.order.update({
      where: { id: order.id },
      data: { status: 'failed' },
    });
    return NextResponse.json(
      { error: 'Não foi possível gerar a recarga na AbacatePay', detail: err?.message },
      { status: 502 }
    );
  }
}
