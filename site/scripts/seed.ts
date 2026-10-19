import { prisma } from '@/lib/db';

async function main() {
  const plans = [
    { name: 'Mensal', slug: 'mensal', price: 4700, currency: 'BRL', interval: 'month', abacatePlanId: 'plan_mensal', features: ['Cortes ilimitados com IA', 'Legendas dinâmicas', 'Até 5 projetos ativos', 'Suporte por e-mail', 'Resolução até 1080p'] },
    { name: 'Trimestral', slug: 'trimestral', price: 11900, currency: 'BRL', interval: 'quarter', abacatePlanId: 'plan_trimestral', features: ['Tudo do Mensal', 'Até 15 projetos ativos', 'Resolução até 1440p', 'Suporte prioritário', 'Templates exclusivos', 'Tradução automática'] },
    { name: 'Anual', slug: 'anual', price: 39700, currency: 'BRL', interval: 'year', abacatePlanId: 'plan_anual', features: ['Tudo do Trimestral', 'Projetos ilimitados', 'Resolução até 4K', 'Suporte 24/7', 'Acesso antecipado', 'IA local (GGUF)'] },
  ];

  for (const p of plans) {
    await prisma.plan.upsert({
      where: { slug: p.slug },
      update: { name: p.name, price: p.price, currency: p.currency, interval: p.interval, abacatePlanId: p.abacatePlanId, features: p.features, active: true },
      create: p,
    });
  }

  const adminEmail = process.env.ADMIN_EMAIL || 'admin@forjaviral.com';
  const adminPass = process.env.ADMIN_PASSWORD || 'admin123';
  const existing = await prisma.customer.findUnique({ where: { email: adminEmail } });
  if (!existing) {
    await prisma.customer.create({ data: { name: 'Admin', email: adminEmail } });
  }

  console.log('Seed completo: planos criados.');
}

main().catch((e) => { console.error(e); process.exit(1); }).finally(async () => { await prisma.$disconnect(); });