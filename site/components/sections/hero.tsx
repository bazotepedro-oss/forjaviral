'use client';

import Link from 'next/link';
import {
  Flame,
  Zap,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  Cpu,
  Smartphone,
  Eye,
  Sliders,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border py-16 md:py-28">
      {/* Background Glows */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-10%,rgba(255,92,0,0.18),rgba(255,0,76,0.06),transparent)]" />
      <div className="pointer-events-none absolute -left-40 top-20 h-96 w-96 rounded-full bg-brand/20 blur-[120px]" />
      <div className="pointer-events-none absolute -right-40 bottom-10 h-96 w-96 rounded-full bg-brand-soft/20 blur-[120px]" />

      <div className="relative mx-auto w-full max-w-6xl px-4">
        <div className="grid items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Copy & Value Proposition */}
          <div className="space-y-6 lg:col-span-7 text-center lg:text-left">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand/40 bg-brand/10 px-4 py-1.5 text-xs font-bold text-brand shadow-glow">
              <Flame className="h-4 w-4 animate-pulse text-brand" />
              <span>Sem Mensalidade Presa • 1 Crédito = 1 Vídeo Pronto</span>
            </div>

            <h1 className="font-display text-4xl font-extrabold leading-[1.12] tracking-tight text-text-primary sm:text-5xl lg:text-6xl">
              Corte podcasts e vídeos longos em{' '}
              <span className="bg-gradient-to-r from-brand via-brand-soft to-orange-400 bg-clip-text text-transparent">
                virais milionários
              </span>{' '}
              com IA em segundos.
            </h1>

            <p className="max-w-xl mx-auto lg:mx-0 text-base sm:text-lg text-text-secondary leading-relaxed">
              Esqueça pagar R$ 150 todo mês em ferramentas gringas. Compre créditos avulsos no Pix, gere cortes 9:16 com enquadramento de rosto (Face Crop) e legendas dinâmicas estilo Hormozi.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3.5 pt-2">
              <Button asChild size="lg" className="w-full sm:w-auto font-bold text-base h-13 px-8 bg-brand-gradient hover:brightness-110 text-white shadow-lg shadow-brand/25">
                <Link href="#planos">
                  <Zap className="h-5 w-5 mr-2" />
                  Ver Pacotes de Créditos
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="w-full sm:w-auto font-semibold text-sm h-13 px-6 border-border hover:bg-surface-elevated">
                <Link href="/recarga">
                  <Sliders className="h-4 w-4 mr-2 text-brand" />
                  Recarregar Licença
                </Link>
              </Button>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-x-6 gap-y-2.5 pt-4 text-xs font-medium text-text-secondary">
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

          {/* Right Column: High-Tech Phone & AI Visualizer Mockup */}
          <div className="relative lg:col-span-5 flex justify-center">
            {/* Background halo */}
            <div className="absolute inset-0 rounded-full bg-brand/20 blur-3xl transform scale-90" />

            {/* Smartphone Frame Simulation */}
            <div className="relative w-full max-w-[320px] rounded-[38px] border-4 border-white/15 bg-surface/90 p-3 shadow-2xl backdrop-blur-xl">
              {/* Phone speaker notch */}
              <div className="mx-auto mb-3 h-4 w-28 rounded-full bg-background/80 border border-white/5 flex items-center justify-center">
                <div className="h-1.5 w-10 rounded-full bg-white/20" />
              </div>

              {/* Video Player Display Area (9:16 Aspect) */}
              <div className="relative aspect-[9/16] overflow-hidden rounded-[28px] bg-gradient-to-b from-stone-900 via-neutral-950 to-black border border-white/10 flex flex-col justify-between p-4 shadow-inner">
                {/* Top Overlay Badges */}
                <div className="flex items-center justify-between z-10">
                  <span className="rounded-full bg-black/60 px-2.5 py-1 text-[10px] font-bold text-white border border-white/10 backdrop-blur-md flex items-center gap-1">
                    <TrendingUp className="h-3 w-3 text-brand" /> Viral Score: <strong className="text-emerald-400">98/100</strong>
                  </span>
                  <span className="rounded-full bg-brand/20 px-2 py-0.5 text-[9px] font-mono text-brand border border-brand/40 font-bold uppercase">
                    AI CLIP #04
                  </span>
                </div>

                {/* Simulated Speaker & Face Tracker Grid */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  {/* Face Tracking Bounding Box */}
                  <div className="relative h-44 w-44 rounded-2xl border-2 border-brand/60 bg-brand/5 shadow-[0_0_30px_rgba(255,92,0,0.15)] flex flex-col justify-between p-1.5 animate-pulse">
                    <div className="flex justify-between text-[8px] font-mono text-brand font-bold">
                      <span>[FACE_CROP]</span>
                      <span>LOCK 99%</span>
                    </div>
                    {/* Corner accents */}
                    <div className="flex justify-center items-center h-full">
                      <div className="h-16 w-16 rounded-full border border-dashed border-brand/40 flex items-center justify-center">
                        <div className="h-2 w-2 rounded-full bg-brand" />
                      </div>
                    </div>
                    <div className="text-right text-[8px] font-mono text-emerald-400">
                      TRACKING: ACTIVE
                    </div>
                  </div>
                </div>

                {/* Bottom Overlay: Hormozi Subtitles Preview */}
                <div className="z-10 space-y-3 pb-2 text-center">
                  {/* Dynamic Audio Waves */}
                  <div className="flex items-center justify-center gap-1">
                    {[16, 28, 42, 22, 34, 48, 20, 38, 24, 14].map((h, i) => (
                      <span
                        key={i}
                        className="w-1 rounded-full bg-gradient-to-t from-brand to-yellow-400 animate-pulse"
                        style={{ height: `${h}px`, animationDelay: `${i * 0.1}s` }}
                      />
                    ))}
                  </div>

                  {/* Hormozi Subtitle Simulation */}
                  <div className="rounded-xl bg-black/75 px-3 py-2 border border-white/10 backdrop-blur-md">
                    <p className="font-display text-sm font-black uppercase tracking-wider text-white">
                      O SEGREDO DE{' '}
                      <span className="text-yellow-400 bg-yellow-400/20 px-1 rounded shadow-[0_0_10px_rgba(250,204,21,0.5)]">
                        1 MILHÃO
                      </span>{' '}
                      DE VIEWS 🚀
                    </p>
                  </div>

                  {/* Export Specs Tag */}
                  <div className="flex items-center justify-center gap-1.5 text-[9px] font-mono text-text-secondary">
                    <span>1080x1920</span>
                    <span>•</span>
                    <span>60 FPS</span>
                    <span>•</span>
                    <span className="text-brand font-bold">XML PREMIERE</span>
                  </div>
                </div>
              </div>

              {/* Bottom Phone Indicator */}
              <div className="mx-auto mt-2.5 h-1 w-24 rounded-full bg-white/20" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}