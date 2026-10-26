'use client';

import Link from 'next/link';
import {
  Flame,
  Zap,
  ArrowRight,
  CheckCircle2,
  Sliders,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border py-16 md:py-24">
      {/* Background Ambient Glows */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-10%,rgba(255,92,0,0.22),rgba(255,0,76,0.08),transparent)]" />
      <div className="pointer-events-none absolute -left-40 top-20 h-[450px] w-[450px] rounded-full bg-brand/25 blur-[140px]" />
      <div className="pointer-events-none absolute -right-40 bottom-10 h-[450px] w-[450px] rounded-full bg-brand-soft/20 blur-[140px]" />

      <div className="relative mx-auto w-full max-w-6xl px-4">
        <div className="grid items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Copy & Value Proposition */}
          <div className="space-y-7 lg:col-span-7 text-center lg:text-left">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand/50 bg-brand/10 px-4 py-1.5 text-xs font-bold text-brand shadow-[0_0_20px_rgba(255,92,0,0.25)]">
              <Flame className="h-4 w-4 animate-pulse text-brand" />
              <span>Sem Mensalidade Presa • 1 Crédito = 1 Vídeo Pronto</span>
            </div>

            <h1 className="font-display text-4xl font-extrabold leading-[1.10] tracking-tight text-text-primary sm:text-5xl lg:text-6xl">
              Corte podcasts e vídeos longos em{' '}
              <span className="bg-gradient-to-r from-brand via-orange-500 to-amber-400 bg-clip-text text-transparent drop-shadow-sm">
                virais milionários
              </span>{' '}
              com IA em segundos.
            </h1>

            <p className="max-w-xl mx-auto lg:mx-0 text-base sm:text-lg text-text-secondary leading-relaxed">
              Esqueça pagar R$ 150 todo mês em ferramentas gringas. Compre créditos avulsos no Pix, gere cortes verticais 9:16 com enquadramento automático de rosto (Face Crop) e legendas dinâmicas estilo Hormozi.
            </p>

            {/* CTAs — Botões Grandes, Marcantes e Imponentes */}
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-3">
              <Link href="/#planos" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  className="w-full sm:w-auto h-15 sm:h-16 px-8 sm:px-10 text-base sm:text-lg font-black tracking-wide text-white bg-gradient-to-r from-brand via-orange-500 to-amber-500 hover:brightness-110 rounded-2xl shadow-[0_0_35px_rgba(255,92,0,0.45)] transition-all duration-300 hover:scale-[1.03] active:scale-[0.98]"
                >
                  <Zap className="h-5 w-5 mr-2 text-white animate-pulse" />
                  Ver Pacotes de Créditos
                  <ArrowRight className="h-5 w-5 ml-2 text-white" />
                </Button>
              </Link>

              <Link href="/recarga" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto h-15 sm:h-16 px-7 sm:px-8 text-base font-bold text-text-primary bg-surface/90 hover:bg-surface-elevated border-2 border-brand/40 hover:border-brand rounded-2xl shadow-xl hover:shadow-brand/20 transition-all duration-300 hover:scale-[1.03] active:scale-[0.98]"
                >
                  <Sliders className="h-4 w-4 mr-2 text-brand" />
                  Recarregar Licença
                </Button>
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-x-6 gap-y-2.5 pt-3 text-xs font-semibold text-text-secondary">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-brand" /> Sem assinatura no cartão
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-brand" /> Roda local ou Google Colab
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-brand" /> Pix com liberação em 5s
              </span>
            </div>
          </div>

          {/* Right Column: Moldura de Celular com o Vídeo Real */}
          <div className="relative lg:col-span-5 flex justify-center">
            {/* Ambient Halo Behind Phone */}
            <div className="absolute inset-0 rounded-full bg-brand/25 blur-3xl transform scale-90" />

            {/* Smartphone Frame — Moldura Limpa e Elegante */}
            <div className="relative w-full max-w-[310px] sm:max-w-[330px] rounded-[48px] border-[6px] border-neutral-700/80 bg-neutral-950 p-2.5 sm:p-3 shadow-[0_25px_70px_rgba(0,0,0,0.9),0_0_60px_rgba(255,92,0,0.25)] ring-1 ring-white/10 backdrop-blur-xl">
              {/* Speaker / Dynamic Island Notch */}
              <div className="mx-auto mb-2.5 h-4 w-28 rounded-full bg-black border border-white/10 flex items-center justify-center gap-2">
                <div className="h-1.5 w-10 rounded-full bg-neutral-700" />
                <div className="h-2 w-2 rounded-full bg-neutral-800 border border-white/5" />
              </div>

              {/* Video Player Display Area (9:16 Aspect) */}
              <div className="relative aspect-[9/16] w-full overflow-hidden rounded-[36px] bg-black shadow-inner border border-white/10">
                <video
                  src="/videos/demo.mp4"
                  autoPlay
                  loop
                  muted
                  playsInline
                  controls={false}
                  className="h-full w-full object-cover"
                />

                {/* Subtle Glass Reflection Overlay */}
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.03] to-transparent" />
              </div>

              {/* Bottom Phone Indicator */}
              <div className="mx-auto mt-2.5 h-1 w-28 rounded-full bg-white/25" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}