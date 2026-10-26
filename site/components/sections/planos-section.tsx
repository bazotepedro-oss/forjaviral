'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { formatPrice, cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Coins, Zap, ShieldCheck, ArrowRight, Sliders, Check, Sparkles, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface Plan {
  id: string;
  name: string;
  slug: string;
  price: number;
  currency: string;
  interval: string;
  features: any;
  active: boolean;
}

interface Props {
  plans: Plan[];
}

function calculateCustomPricing(credits: number) {
  const c = Math.max(5, Math.min(5000, Math.floor(credits || 5)));
  let unit = 1.30;
  let discount = 0;
  let tier = 'Preço Normal';

  if (c >= 2500) {
    unit = 0.33;
    discount = 75;
    tier = 'Mega Volume Industrial (75% OFF)';
  } else if (c >= 1000) {
    unit = 0.39;
    discount = 70;
    tier = 'Plano Enterprise (70% OFF)';
  } else if (c >= 500) {
    unit = 0.45;
    discount = 65;
    tier = 'Super Atacado (65% OFF)';
  } else if (c >= 250) {
    unit = 0.55;
    discount = 58;
    tier = 'Desconto Agência (58% OFF)';
  } else if (c >= 100) {
    unit = 0.66;
    discount = 49;
    tier = 'Desconto de Atacado (49% OFF)';
  } else if (c >= 50) {
    unit = 0.79;
    discount = 39;
    tier = 'Super Desconto Criador (39% OFF)';
  } else if (c >= 30) {
    unit = 0.95;
    discount = 27;
    tier = 'Desconto Especial (27% OFF)';
  }

  const total = c * unit;
  const normalTotal = c * 1.30;
  const economy = normalTotal - total;

  return { credits: c, unitPrice: unit, total, normalTotal, economy, discount, tier };
}

// 3 Core Showcase Plans
const CORE_PLANS = [
  {
    slug: 'pack_teste',
    name: 'Pack Teste',
    credits: 15,
    price: 1990,
    costPerVideo: '1,32',
    isPopular: false,
    tag: null,
    features: [
      '15 cortes virais com IA (1 crédito = 1 vídeo)',
      'Legendas dinâmicas estilo Hormozi / TikTok',
      'Enquadramento de rosto Face Crop (9:16)',
      'Válido por 365 dias (Sem mensalidade)',
      'Entrega imediata via Pix',
    ],
  },
  {
    slug: 'pack_criador',
    name: 'Pack Criador',
    credits: 50,
    price: 3990,
    costPerVideo: '0,79',
    isPopular: true,
    tag: 'Mais Vendido 🔥',
    features: [
      '50 cortes virais com IA (39% de Desconto)',
      'Ideal para quem posta todo dia no Reels/TikTok',
      'Renderização prioritária com GPU acelerada',
      'Suporte direto no WhatsApp em Português',
      'Exportação 1080p 60fps sem marca d’água',
    ],
  },
  {
    slug: 'pack_escala',
    name: 'Pack Escala',
    credits: 120,
    price: 7990,
    costPerVideo: '0,66',
    isPopular: false,
    tag: 'Melhor Custo 🚀',
    features: [
      '120 cortes virais com IA (49% de Desconto)',
      'Máxima economia para canais dark e agências',
      'Exportação XML aberta para Premiere e DaVinci',
      'Acesso antecipado a novos modelos de IA',
      'Créditos cumulativos por 1 ano inteiro',
    ],
  },
];

const QUICK_PRESETS = [50, 100, 250, 500, 1000, 2500, 5000];

export function PlanosSection({ plans }: Props) {
  const [customCredits, setCustomCredits] = useState<number>(250);
  const customPricing = useMemo(() => calculateCustomPricing(customCredits), [customCredits]);

  return (
    <section id="planos" className="border-b border-border py-20 md:py-28 relative overflow-hidden">
      {/* Background radial highlight */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_15%,rgba(255,92,0,0.14),transparent)] pointer-events-none" />

      <div className="relative mx-auto w-full max-w-6xl px-4">
        {/* Cabeçalho da Seção */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/50 bg-brand/10 px-4 py-1.5 text-xs font-extrabold text-brand shadow-[0_0_20px_rgba(255,92,0,0.25)]">
            <Coins className="w-4 h-4 text-brand" />
            <span>1 Crédito = 1 Vídeo Cortado e Renderizado com IA</span>
          </div>

          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-black text-text-primary tracking-tight">
            Escolha seu pacote. <span className="bg-gradient-to-r from-brand via-orange-500 to-amber-400 bg-clip-text text-transparent">Sem mensalidade.</span>
          </h2>

          <p className="text-text-secondary text-base sm:text-lg max-w-2xl mx-auto">
            Pague uma única vez no Pix. Seus créditos nunca expiram no fim do mês e você só recarrega quando precisar.
          </p>
        </div>

        {/* Grid dos 3 Cards Principais — Visual Imponente e Botões Grandes */}
        <div className="mt-14 grid gap-7 md:grid-cols-3 items-stretch">
          {CORE_PLANS.map((plan) => {
            return (
              <div
                key={plan.slug}
                className={cn(
                  'relative flex flex-col justify-between rounded-[32px] p-7 sm:p-8 transition-all duration-300',
                  plan.isPopular
                    ? 'border-2 border-brand bg-gradient-to-b from-[#1E1F24] via-[#16171B] to-[#0E0F12] shadow-[0_0_50px_rgba(255,92,0,0.30)] md:-translate-y-3 z-10'
                    : 'border-2 border-white/10 bg-gradient-to-b from-[#18191D] to-[#0F1012] hover:border-brand/50 shadow-xl'
                )}
              >
                {plan.tag && (
                  <span className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-brand to-amber-500 px-4 py-1 text-xs font-black text-white shadow-[0_4px_15px_rgba(255,92,0,0.4)] tracking-wide uppercase">
                    {plan.tag}
                  </span>
                )}

                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <h3 className="font-display text-xl font-extrabold text-text-primary">{plan.name}</h3>
                    <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-brand bg-brand/15 px-2.5 py-1 rounded-lg border border-brand/30">
                      <Zap className="w-3.5 h-3.5 text-brand" /> {plan.credits} vídeos
                    </div>
                  </div>

                  <div>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-4xl sm:text-5xl font-black text-white tracking-tight">
                        {formatPrice(plan.price, 'BRL')}
                      </span>
                      <span className="text-xs text-text-secondary font-bold uppercase tracking-wider">/ pix único</span>
                    </div>
                    <p className="mt-2 text-xs font-bold text-brand bg-brand/10 inline-block px-2.5 py-1 rounded-md border border-brand/20">
                      Apenas R$ {plan.costPerVideo} por corte pronto
                    </p>
                  </div>

                  <ul className="space-y-3 text-xs sm:text-sm text-text-secondary border-t border-white/10 pt-5">
                    {plan.features.map((f, idx) => (
                      <li key={idx} className="flex items-start gap-2.5">
                        <div className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-brand/20 text-brand">
                          <Check className="h-3 w-3 text-brand stroke-[3]" />
                        </div>
                        <span className="text-neutral-200">{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Botões Grandes e Destacados */}
                <div className="pt-8 mt-4">
                  <Link href={`/checkout?plan=${plan.slug}`} className="block">
                    <Button
                      size="lg"
                      className={cn(
                        'w-full font-black text-base h-14 sm:h-15 rounded-2xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]',
                        plan.isPopular
                          ? 'bg-gradient-to-r from-brand via-orange-500 to-amber-500 hover:brightness-110 text-white shadow-[0_4px_25px_rgba(255,92,0,0.5)]'
                          : 'bg-surface-elevated hover:bg-surface-elevated/90 hover:border-brand/60 border-2 border-white/10 text-text-primary shadow-lg'
                      )}
                    >
                      Comprar {plan.credits} Créditos
                    </Button>
                  </Link>
                  <p className="mt-2.5 text-center text-[11px] text-text-secondary flex items-center justify-center gap-1.5 font-medium">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Chave imediata • Válido por 1 ano
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── SELEÇÃO PERSONALIZADA (5 A 5.000 CRÉDITOS) ── */}
        <div className="mt-14 rounded-[36px] border-2 border-brand/40 bg-gradient-to-b from-[#1C1D22] via-[#141518] to-[#0F1013] p-7 sm:p-10 shadow-[0_0_60px_rgba(255,92,0,0.18)]">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-brand/15 px-3 py-1 text-xs font-bold text-brand border border-brand/30 mb-2">
                <Sliders className="h-3.5 w-3.5" /> Escolha Livre: de 5 até 5.000 Créditos
              </div>
              <h3 className="font-display text-2xl sm:text-3xl font-extrabold text-white">
                Precisa de uma quantidade personalizada?
              </h3>
              <p className="text-sm text-text-secondary mt-1">
                Escolha qualquer volume entre 5 e 5.000 cortes com desconto progressivo automático no atacado.
              </p>
            </div>

            <Badge variant="outline" className="border-brand/50 bg-brand/10 text-brand font-bold text-sm px-4 py-1.5 self-start md:self-auto">
              {customPricing.tier}
            </Badge>
          </div>

          {/* Atalhos Rápidos para Volumes Frequentes */}
          <div className="pt-6">
            <span className="text-xs font-bold text-text-secondary uppercase tracking-wider block mb-3">
              Volumes mais escolhidos:
            </span>
            <div className="flex flex-wrap gap-2 sm:gap-2.5">
              {QUICK_PRESETS.map((p) => {
                const isSelected = customCredits === p;
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setCustomCredits(p)}
                    className={cn(
                      'px-4 py-2 rounded-xl text-xs sm:text-sm font-bold border transition-all duration-200',
                      isSelected
                        ? 'border-brand bg-brand text-white shadow-[0_0_20px_rgba(255,92,0,0.4)] scale-105'
                        : 'border-white/10 bg-surface/80 text-text-secondary hover:border-brand/50 hover:text-white'
                    )}
                  >
                    {p >= 1000 ? `${p / 1000}k` : p} vídeos
                  </button>
                );
              })}
            </div>
          </div>

          {/* Controles: Slider + Input Numérico Direto */}
          <div className="mt-8 grid gap-8 lg:grid-cols-12 items-center bg-black/40 p-6 sm:p-8 rounded-2xl border border-white/10">
            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">Quantidade de Cortes Desejada:</span>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    min={5}
                    max={5000}
                    value={customCredits}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setCustomCredits(isNaN(val) ? 5 : Math.max(5, Math.min(5000, val)));
                    }}
                    className="w-28 text-center text-xl font-black font-mono h-12 bg-surface border-2 border-brand/50 focus:border-brand text-white rounded-xl shadow-inner"
                  />
                  <span className="text-xs font-bold text-text-secondary uppercase">créditos</span>
                </div>
              </div>

              {/* Slider Slider suave até 5.000 */}
              <input
                type="range"
                min={5}
                max={5000}
                step={5}
                value={customCredits}
                onChange={(e) => setCustomCredits(Number(e.target.value))}
                className="w-full h-3 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-brand"
              />

              <div className="flex justify-between text-[11px] font-bold text-text-secondary pt-1">
                <span>5 vídeos (Mínimo)</span>
                <span>500 vídeos</span>
                <span>2.500 vídeos</span>
                <span className="text-brand">5.000 vídeos (Máximo)</span>
              </div>
            </div>

            {/* Resumo e Botão de Ação */}
            <div className="lg:col-span-5 flex flex-col justify-between space-y-4 lg:pl-6 lg:border-l lg:border-white/10">
              <div>
                <div className="flex items-baseline justify-between">
                  <span className="text-xs font-bold text-text-secondary">Valor por Vídeo:</span>
                  <span className="text-sm font-extrabold text-brand">
                    R$ {customPricing.unitPrice.toFixed(2).replace('.', ',')}
                  </span>
                </div>

                <div className="flex items-baseline justify-between mt-1">
                  <span className="text-xs font-bold text-text-secondary">Economia no Atacado:</span>
                  <span className="text-xs font-bold text-emerald-400">
                    - R$ {customPricing.economy.toFixed(2).replace('.', ',')} ({customPricing.discount}% OFF)
                  </span>
                </div>

                <div className="mt-3 pt-3 border-t border-white/10 flex items-baseline justify-between">
                  <span className="text-sm font-bold text-white">Total via Pix:</span>
                  <span className="text-3xl font-black text-white">
                    {customPricing.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                </div>
              </div>

              {/* Botão de Compra Personalizada */}
              <Link
                href={`/recarga?credits=${customPricing.credits}`}
                className="block w-full"
              >
                <Button
                  size="lg"
                  className="w-full h-15 font-black text-base bg-gradient-to-r from-brand via-orange-500 to-amber-500 hover:brightness-110 text-white rounded-2xl shadow-[0_4px_30px_rgba(255,92,0,0.45)] transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Sparkles className="h-5 w-5 mr-2" />
                  Gerar Pix ({customPricing.credits} Créditos)
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}