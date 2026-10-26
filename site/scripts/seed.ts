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
        '15 cortes virais com IA (R$ 1,32 por corte)',
        'Legendas dinâmicas estilo Hormozi / TikTok',
        'Enquadramento Face Crop automático (9:16)',
        'Áudio aprimorado e corte de silêncio',
        'Exportação XML para Premiere / DaVinci',
        'Créditos válidos por 365 dias (Sem mensalidade)',
      ],
    },
    {
      name: 'Pack Iniciante (30 Vídeos)',
      slug: 'pack_iniciante',
      price: 2990,
      currency: 'BRL',
      interval: 'one_time',
      abacatePlanId: 'pack_iniciante_30',
      features: [
        '30 cortes virais com IA (R$ 0,99 por corte - 25% OFF)',
        'Ideal para testar 1 vídeo por dia durante o mês',
        'Todas as funções de IA e corte inclusas',
        'Renderização acelerada por GPU',
        'Suporte direto via WhatsApp',
        'Sem assinatura e sem pegadinhas',
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
        '50 cortes virais com IA (R$ 0,79 por corte - 39% OFF)',
        'Mais Vendido 🔥 — Perfeito para TikTok e Reels',
        'Prioridade máxima no servidor',
        'Exportação em 1080p 60fps',
        'Templates prontos de legendas',
        'Créditos acumulativos por 1 ano',
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
        '120 cortes virais com IA (R$ 0,66 por corte - 49% OFF)',
        'Máxima economia para canais dark e múltiplos perfis',
        'Suporte VIP prioritário',
        'Acesso antecipado a novas atualizações',
        'Volume para postar 4 vídeos por dia',
        'Créditos válidos por 365 dias',
      ],
    },
    {
      name: 'Pack Agência / Pro (250 Vídeos)',
      slug: 'pack_pro',
      price: 13990,
      currency: 'BRL',
      interval: 'one_time',
      abacatePlanId: 'pack_pro_250',
      features: [
        '250 cortes virais com IA (R$ 0,55 por corte - 58% OFF)',
        'Volume industrial para agências e infoprodutores',
        'Custo imbatível: apenas R$ 0,55 por vídeo completo',
        'Suporte dedicado com canal direto',
        'Sem limite de exportação diária',
        'Validade total de 1 ano',
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

  const adminEmail = process.env.ADMIN_EMAIL || 'admin@fabricadecortes.com';
  const existing = await prisma.customer.findUnique({ where: { email: adminEmail } });
  if (!existing) {
    await prisma.customer.create({ data: { name: 'Admin', email: adminEmail } });
  }

  console.log('Seed completo: 5 pacotes de créditos configurados.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });