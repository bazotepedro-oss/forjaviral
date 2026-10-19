// POST /api/checkout/recharge — Cria sessão de recarga de créditos com desconto progressivo no AbacatePay
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { prisma } from '@/lib/db';
import { rateLimit } from '@/lib/ratelimit';
import { createCheckout } from '@/lib/abacatepay';

const Schema = z.object({
  identifier: z.string().min(3, 'Informe sua Chave de Licença, Usuário ou E-mail'),
  credits: z.number().min(5, 'Mínimo de 5 créditos').max(1000, 'Máximo de 1.000 créditos'),
  name: z.string().min(2, 'Nome muito curto'),
  email: z.string().email('E-mail inválido'),
  phone: z.string().optional(),
});

function calculateProgressivePrice(credits: number) {
  const c = Math.max(5, Math.min(1000, Math.floor(credits)));
  let unit = 1.30;
  let discount = 0;
  let tier = 'Sem desconto';

  if (c >= 100) {
    unit = 0.66;
    discount = 49;
    tier = 'Desconto Máximo de Atacado (49% OFF)';
  } else if (c >= 50) {
    unit = 0.79;
    discount = 39;
    tier = 'Super Desconto (39% OFF)';
  } else if (c >= 30) {
    unit = 0.95;
    discount = 27;
    tier = 'Desconto Especial (27% OFF)';
  }

  const totalCents = Math.round(c * unit * 100);
  return {
    credits: c,
    unitPrice: unit,
    totalCents,
    discountPercent: discount,
    tier,
  };
}

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

  const { identifier, credits, name, email, phone } = parsed.data;
  const pricing = calculateProgressivePrice(credits);

  // 1. Resolver Chave de Licença real (pode ter vindo chave FV-, e-mail ou username)
  const cleanId = identifier.trim();
  let resolvedLicenseKey = cleanId;

  // Busca se é um username ou email existente
  const cred = await prisma.accessCredentials.findFirst({
    where: {
      OR: [
        { licenseKey: cleanId },
        { username: cleanId },
        { customer: { email: cleanId } },
      ],
    },
    include: { customer: true },
  });

  if (cred?.licenseKey) {
    resolvedLicenseKey = cred.licenseKey;
  }

  // 2. Localiza ou cria o cliente
  let customer = await prisma.customer.findUnique({ where: { email } });
  if (!customer) {
    customer = await prisma.customer.create({ data: { name, email, phone } });
  } else if (phone && !customer.phone) {
    await prisma.customer.update({ where: { id: customer.id }, data: { phone } });
  }

  // 3. Garante que o plano de recarga dinâmico existe no banco
  const packageSlug = `recarga_${pricing.credits}_creditos`;
  let plan = await prisma.plan.findUnique({ where: { slug: packageSlug } });
  if (!plan) {
    plan = await prisma.plan.create({
      data: {
        name: `Recarga ${pricing.credits} Créditos`,
        slug: packageSlug,
        price: pricing.totalCents,
        currency: 'BRL',
        interval: 'one_time',
        features: JSON.stringify([`+${pricing.credits} Créditos automáticos no Forja Viral (${pricing.tier})`]),
        active: true,
      },
    });
  }

  // 4. Cria a ordem de recarga
  const order = await prisma.order.create({
    data: {
      customerId: customer.id,
      planId: plan.id,
      status: 'pending',
      amount: pricing.totalCents,
      currency: 'BRL',
      metadata: {
        isRecharge: true,
        licenseKey: resolvedLicenseKey,
        creditsToAdd: pricing.credits,
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
      amount: pricing.totalCents,
      currency: 'BRL',
      customer: { name, email, phone },
      metadata: {
        orderId: order.id,
        isRecharge: 'true',
        licenseKey: resolvedLicenseKey,
        creditsToAdd: String(pricing.credits),
      },
      returnURL,
      appName: `Forja Viral - Recarga ${pricing.credits} Créditos`,
    });

    await prisma.order.update({
      where: { id: order.id },
      data: { abacateCheckoutId: checkout.checkoutId },
    });

    return NextResponse.json({
      ok: true,
      checkoutURL: checkout.checkoutURL,
      checkoutId: checkout.checkoutId,
      orderId: order.id,
      resolvedLicenseKey,
      credits: pricing.credits,
      totalCents: pricing.totalCents,
    });
  } catch (err: any) {
    console.error('[Checkout Recharge] Erro ao criar checkout no AbacatePay:', err);
    return NextResponse.json({ error: err?.message || 'Falha ao gerar cobrança Pix' }, { status: 502 });
  }
}
