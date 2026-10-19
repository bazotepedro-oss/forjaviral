'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { formatPrice, cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Coins, Zap, ShieldCheck, Sparkles, ArrowRight, Sliders } from 'lucide-react';
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
    tier = '49% OFF (Atacado)';
  } else if (c >= 50) {
    unit = 0.79;
    discount = 39;
    tier = '39% OFF (Super Desconto)';
  } else if (c >= 30) {
    unit = 0.95;
    discount = 27;
    tier = '27% OFF (Desconto Progressivo)';
  }

  const total = c * unit;
  return { credits: c, unitPrice: unit, total, discount, tier };
}

export function PlanosSection({ plans }: Props) {
  const [customCredits, setCustomCredits] = useState<number>(60);
  const customPricing = useMemo(() => calculateCustomPricing(customCredits), [customCredits]);

  return (
    <section id="planos" className="border-b border-border py-20 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(255,92,0,0.12),rgba(255,255,255,0))]" />

      <div className="relative mx-auto w-full max-w-6xl px-4">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/10 px-4 py-1.5 text-xs font-semibold text-brand mb-4">
            <Coins className="w-3.5 h-3.5" />
            1 Crédito = 1 Vídeo Viral Pronto
          </div>
          <h2 className="font-display text-3xl font-extrabold text-text-primary md:text-5xl">
            Pacotes de Créditos <span className="text-transparent bg-clip-text bg-brand-gradient">Sem Mensalidade</span>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-text-secondary text-base">
            Esqueça assinaturas presas no cartão. Pague apenas pelos vídeos que produzir. Seus créditos nunca somem no fim do mês.
          </p>
        </div>

        {/* Grid de Planos Principais */}
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 items-stretch">
          {plans.map((plan) => {
            const isPopular = plan.slug === 'pack_criador';
            const isBestValue = plan.slug === 'pack_escala' || plan.slug === 'pack_pro';
            const features = Array.isArray(plan.features) ? (plan.features as string[]) : [];

            // Quantidade de vídeos baseado no slug ou preço
            let videoCount = 50;
            if (plan.slug.includes('teste') || plan.slug.includes('15')) videoCount = 15;
            else if (plan.slug.includes('iniciante') || plan.slug.includes('30')) videoCount = 30;
            else if (plan.slug.includes('criador') || plan.slug.includes('50')) videoCount = 50;
            else if (plan.slug.includes('escala') || plan.slug.includes('120')) videoCount = 120;
            else if (plan.slug.includes('pro') || plan.slug.includes('250')) videoCount = 250;

            const costPerVideo = (plan.price / 100 / videoCount).toFixed(2).replace('.', ',');

            return (
              <div
                key={plan.id}
                className={cn(
                  'relative flex flex-col justify-between rounded-3xl border p-7 transition-all duration-300',
                  isPopular
                    ? 'border-brand bg-surface/90 shadow-[0_0_50px_rgba(255,92,0,0.22)] md:-translate-y-2'
                    : 'border-white/10 bg-surface/60 hover:border-white/20 hover:bg-surface/80'
                )}
              >
                {isPopular && (
                  <Badge variant="brand" className="absolute -top-3.5 left-1/2 -translate-x-1/2 shadow-glow text-xs uppercase tracking-wider py-1 px-3">
                    🔥 O Mais Escolhido
                  </Badge>
                )}
                {isBestValue && (
                  <Badge variant="outline" className="absolute -top-3.5 left-1/2 -translate-x-1/2 border-brand/40 bg-brand/10 text-brand text-[11px] font-bold uppercase tracking-wider py-0.5 px-3">
                    🚀 Maior Desconto
                  </Badge>
                )}

                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="font-display text-xl font-bold text-text-primary">{plan.name}</h3>
                    <div className="w-8 h-8 rounded-xl bg-brand/10 flex items-center justify-center text-brand">
                      <Zap className="w-4 h-4" />
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-extrabold text-text-primary">
                        {formatPrice(plan.price, plan.currency)}
                      </span>
                      <span className="text-xs text-text-secondary uppercase tracking-wider font-semibold">/ pix único</span>
                    </div>
                    <div className="mt-1.5 text-xs text-brand font-semibold">
                      Apenas R$ {costPerVideo} por corte pronto
                    </div>
                  </div>

                  <ul className="mt-6 space-y-3 text-left border-t border-white/5 pt-5">
                    {features.map((f, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs sm:text-sm text-text-secondary">
                        <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-brand/20 text-[10px] text-brand font-bold">
                          ✓
                        </span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="mt-8 pt-4">
                  <a href={`#checkout?plan=${plan.slug}`} className="block">
                    <button
                      className={cn(
                        'w-full py-3 px-5 rounded-xl font-bold text-sm transition-all duration-200 shadow-md',
                        isPopular
                          ? 'bg-brand-gradient text-white hover:brightness-110 shadow-glow'
                          : 'border border-white/15 bg-white/5 text-text-primary hover:bg-white/10 hover:border-white/25'
                      )}
                    >
                      Garantir {videoCount} Créditos via Pix
                    </button>
                  </a>
                  <p className="mt-2 text-center text-[11px] text-text-secondary flex items-center justify-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Chave imediata e sem assinatura
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Calculadora de Quantidade Personalizada (Aleatória ou Sob Medida) */}
        <div className="mt-14 rounded-3xl border border-brand/40 bg-gradient-to-br from-brand/10 via-surface/90 to-surface p-6 sm:p-8 shadow-2xl backdrop-blur-md">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
            <div className="space-y-3 max-w-xl">
              <Badge variant="brand" className="mb-1 text-xs">
                <Sliders className="w-3 h-3 mr-1" /> Escolha Qualquer Quantidade
              </Badge>
              <h3 className="font-display text-2xl sm:text-3xl font-extrabold text-text-primary">
                Quer uma quantidade aleatória ou sob medida?
              </h3>
              <p className="text-text-secondary text-sm">
                Precisa de um número exato para seus projetos? Digite qualquer quantidade entre 5 e 1.000 créditos e ganhe o desconto progressivo automático.
              </p>

              {/* Slider e Input */}
              <div className="pt-2 space-y-3">
                <div className="flex items-center gap-3">
                  <Input
                    type="number"
                    min={5}
                    max={1000}
                    value={customCredits}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setCustomCredits(isNaN(val) ? 5 : val);
                    }}
                    className="w-28 text-center text-lg font-bold font-mono h-11 border-brand/50 bg-background focus:ring-brand"
                  />
                  <span className="text-sm font-semibold text-text-primary">vídeos / créditos</span>
                  <Badge variant="outline" className="border-brand/40 bg-brand/10 text-brand text-xs">
                    {customPricing.tier}
                  </Badge>
                </div>
                <input
                  type="range"
                  min={5}
                  max={300}
                  step={1}
                  value={customCredits > 300 ? 300 : customCredits}
                  onChange={(e) => setCustomCredits(Number(e.target.value))}
                  className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer accent-brand"
                />
              </div>
            </div>

            {/* Total e Botão de Checkout Instantâneo */}
            <div className="rounded-2xl border border-white/10 bg-background/80 p-6 flex flex-col justify-between space-y-4 min-w-[280px]">
              <div>
                <span className="text-xs uppercase tracking-wider text-text-secondary font-semibold">
                  Total com Desconto Progressivo
                </span>
                <div className="text-3xl sm:text-4xl font-extrabold text-text-primary mt-1">
                  {customPricing.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </div>
                <p className="text-xs text-text-secondary mt-1">
                  Equivale a <strong className="text-brand">R$ {customPricing.unitPrice.toFixed(2).replace('.', ',')}</strong> por vídeo pronto.
                </p>
              </div>

              <Button asChild size="lg" className="w-full font-bold bg-brand hover:bg-brand/90 text-white shadow-lg shadow-brand/20">
                <Link href={`/recarga?credits=${customPricing.credits}`}>
                  <Sparkles className="w-4 h-4 mr-1.5" />
                  Gerar Pix ({customPricing.credits} Créditos)
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}