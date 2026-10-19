'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { formatPrice, cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Coins, Zap, ShieldCheck, ArrowRight, Sliders, Check } from 'lucide-react';
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
  const c = Math.max(5, Math.min(1000, Math.floor(credits || 5)));
  let unit = 1.30;
  let discount = 0;
  let tier = 'Preço Normal';

  if (c >= 100) {
    unit = 0.66;
    discount = 49;
    tier = '49% OFF';
  } else if (c >= 50) {
    unit = 0.79;
    discount = 39;
    tier = '39% OFF';
  } else if (c >= 30) {
    unit = 0.95;
    discount = 27;
    tier = '27% OFF';
  }

  const total = c * unit;
  return { credits: c, unitPrice: unit, total, discount, tier };
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
      'Máxima economia para canais dark e múltiplos perfis',
      'Exportação XML aberta para Premiere e DaVinci',
      'Acesso antecipado a novos modelos de IA',
    ],
  },
];

export function PlanosSection({ plans }: Props) {
  const [showCustom, setShowCustom] = useState(false);
  const [customCredits, setCustomCredits] = useState<number>(60);
  const customPricing = useMemo(() => calculateCustomPricing(customCredits), [customCredits]);

  return (
    <section id="planos" className="border-b border-border py-16 md:py-24 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_10%,rgba(255,92,0,0.10),transparent)]" />

      <div className="relative mx-auto w-full max-w-5xl px-4">
        {/* Cabeçalho Compacto */}
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <Badge variant="brand" className="text-xs">
            <Coins className="w-3.5 h-3.5 mr-1" /> 1 Crédito = 1 Vídeo Cortado com IA
          </Badge>
          <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-text-primary tracking-tight">
            Escolha seu pacote. <span className="text-brand">Sem mensalidade.</span>
          </h2>
          <p className="text-text-secondary text-sm sm:text-base">
            Pague uma única vez no Pix. Seus créditos nunca expiram no fim do mês e você só recarrega quando precisar.
          </p>
        </div>

        {/* Grid Elegante de 3 Cards Perfeitos */}
        <div className="mt-12 grid gap-6 md:grid-cols-3 items-stretch">
          {CORE_PLANS.map((plan) => {
            return (
              <div
                key={plan.slug}
                className={cn(
                  'relative flex flex-col justify-between rounded-3xl p-6 sm:p-7 transition-all duration-300',
                  plan.isPopular
                    ? 'border-2 border-brand bg-gradient-to-b from-surface via-surface to-brand/10 shadow-[0_0_40px_rgba(255,92,0,0.18)] md:-translate-y-2'
                    : 'border border-border/80 bg-surface/70 hover:border-brand/40 hover:bg-surface'
                )}
              >
                {plan.tag && (
                  <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-brand px-3.5 py-0.5 text-xs font-bold text-white shadow-glow tracking-wide">
                    {plan.tag}
                  </span>
                )}

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-display text-lg font-bold text-text-primary">{plan.name}</h3>
                    <div className="flex items-center gap-1 text-xs font-mono font-semibold text-brand bg-brand/10 px-2 py-0.5 rounded-md border border-brand/20">
                      <Zap className="w-3 h-3 text-brand" /> {plan.credits} vídeos
                    </div>
                  </div>

                  <div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-extrabold text-text-primary">
                        {formatPrice(plan.price, 'BRL')}
                      </span>
                      <span className="text-xs text-text-secondary font-medium uppercase tracking-wider">/ pix</span>
                    </div>
                    <p className="mt-1 text-xs font-semibold text-brand">
                      Apenas R$ {plan.costPerVideo} por corte pronto
                    </p>
                  </div>

                  <ul className="space-y-2.5 text-xs text-text-secondary border-t border-border/60 pt-4">
                    {plan.features.map((f, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Check className="h-4 w-4 shrink-0 text-brand mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-6 mt-4">
                  <a href={`#checkout?plan=${plan.slug}`} className="block">
                    <Button
                      size="lg"
                      className={cn(
                        'w-full font-bold text-sm h-11',
                        plan.isPopular
                          ? 'bg-brand hover:bg-brand/90 text-white shadow-lg shadow-brand/25'
                          : 'bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-text-primary'
                      )}
                    >
                      Comprar {plan.credits} Créditos
                    </Button>
                  </a>
                  <p className="mt-2 text-center text-[10px] text-text-secondary flex items-center justify-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    Chave imediata • Válido por 1 ano
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Rodapé Minimalista: Outros Volumes ou Calculadora */}
        <div className="mt-8 rounded-2xl border border-border/80 bg-surface/60 p-4 text-center">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-text-secondary">
              <span className="font-semibold text-text-primary">Outros pacotes:</span>
              <a href="#checkout?plan=pack_iniciante" className="underline hover:text-brand font-medium">
                30 vídeos (R$ 29,90)
              </a>
              <span>•</span>
              <a href="#checkout?plan=pack_pro" className="underline hover:text-brand font-medium">
                Pack Agência 250 vídeos (R$ 139,90)
              </a>
            </div>

            <button
              onClick={() => setShowCustom(!showCustom)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-brand hover:text-brand/80 transition-colors"
            >
              <Sliders className="h-3.5 w-3.5" />
              {showCustom ? 'Fechar calculadora' : 'Precisa de outra quantidade exata?'}
            </button>
          </div>

          {/* Drawer / Calculadora Recolhível (Apenas se clicado) */}
          {showCustom && (
            <div className="mt-4 pt-4 border-t border-border/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-left">
              <div className="space-y-1.5 w-full sm:w-auto">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-text-primary">Quantidade personalizada:</span>
                  <Input
                    type="number"
                    min={5}
                    max={1000}
                    value={customCredits}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setCustomCredits(isNaN(val) ? 5 : val);
                    }}
                    className="w-20 text-center font-bold text-sm h-8 bg-background border-brand/40"
                  />
                  <span className="text-xs text-brand font-bold">({customPricing.tier})</span>
                </div>
                <input
                  type="range"
                  min={5}
                  max={250}
                  step={1}
                  value={customCredits > 250 ? 250 : customCredits}
                  onChange={(e) => setCustomCredits(Number(e.target.value))}
                  className="w-full sm:w-64 h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-brand"
                />
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                <div className="text-right">
                  <span className="text-xs text-text-secondary block">Total via Pix:</span>
                  <span className="text-lg font-extrabold text-text-primary">
                    {customPricing.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                </div>
                <Button asChild size="sm" className="font-bold text-xs bg-brand hover:bg-brand/90 text-white">
                  <Link href={`/recarga?credits=${customPricing.credits}`}>
                    Gerar Pix ({customPricing.credits}) <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Link>
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}