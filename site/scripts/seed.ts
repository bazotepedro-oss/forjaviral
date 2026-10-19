import { prisma } from '@/lib/db';

async function main() {
  const plans = [
    {
      name: 'Pack Teste (15 Vídeos)',
      slug: 'pack_teste',
      price: 1990,
      currency: 'BRL',
      interval: 'one_time',
      abacatePlanId: 'pack_teste_15',
      features: [
        '15 cortes virais com IA (1 crédito = 1 vídeo)',
        'Legendas dinâmicas estilo Hormozi / TikTok',
        'Enquadramento de rosto Face Crop (9:16)',
        'Áudio aprimorado e corte de silêncio',
        'Exportação XML para Premiere / DaVinci',
        'Créditos válidos por 365 dias (Sem mensalidade)',
      ],
    },
    {
      name: 'Pack Criador (50 Vídeos)',
      slug: 'pack_criador',
      price: 3990,
      currency: 'BRL',
      interval: 'one_time',
      abacatePlanId: 'pack_criador_50',
      features: [
        '50 cortes virais com IA (R$ 0,79 por corte)',
        'Ideal para quem posta todo dia no Reels e TikTok',
        'Todas as funções do Pack Teste incluídas',
        'Prioridade de renderização',
        'Suporte direto via WhatsApp',
        'Créditos acumulativos (Sem assinatura no cartão)',
      ],
    },
    {
      name: 'Pack Escala (120 Vídeos)',
      slug: 'pack_escala',
      price: 7990,
      currency: 'BRL',
      interval: 'one_time',
      abacatePlanId: 'pack_escala_120',
      features: [
        '120 cortes virais com IA (R$ 0,66 por corte)',
        'Máxima economia para canais dark e agências',
        'Volume para múltiplos perfis diários',
        'Templates exclusivos de legendas',
        'Acesso antecipado a novos modelos',
        'Créditos válidos por 1 ano inteiro',
      ],
    },
  ];

  for (const p of plans) {
    await prisma.plan.upsert({
      where: { slug: p.slug },
      update: {
        name: p.name,
        price: p.price,
        currency: p.currency,
        interval: p.interval,
        abacatePlanId: p.abacatePlanId,
        features: p.features,
        active: true,
      },
      create: p,
    });
  }

  // Desativa planos mensais antigos para não aparecerem na home
  await prisma.plan.updateMany({
    where: { slug: { in: ['mensal', 'trimestral', 'anual'] } },
    data: { active: false },
  });

  const adminEmail = process.env.ADMIN_EMAIL || 'admin@forjaviral.com';
  const existing = await prisma.customer.findUnique({ where: { email: adminEmail } });
  if (!existing) {
    await prisma.customer.create({ data: { name: 'Admin', email: adminEmail } });
  }

  console.log('Seed completo: pacotes de créditos criados.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });