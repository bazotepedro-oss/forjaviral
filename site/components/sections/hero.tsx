import Link from 'next/link';
import { Flame, Video, Zap, Sparkles, Play, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="pointer-events-none absolute inset-0 bg-brand-radial" />
      <div className="pointer-events-none absolute -left-32 top-0 h-96 w-96 rounded-full bg-brand/20 blur-3xl" />
      <div className="mx-auto w-full max-w-6xl px-4 py-20 md:py-32">
        <div className="grid items-center gap-10 md:grid-cols-2">
          <div className="space-y-6">
            <Badge variant="brand">IA de ponta • Acesso imediato</Badge>
            <h1 className="font-display text-4xl font-bold leading-tight tracking-tight text-text-primary md:text-5xl lg:text-6xl">
              Corte vídeos longos em{' '}
              <span className="bg-gradient-to-r from-brand to-brand-soft bg-clip-text text-transparent">
                cortes virais
              </span>{' '}
              com IA em segundos.
            </h1>
            <p className="max-w-xl text-lg text-text-secondary">
              Assine agora, receba seu acesso automático e comece a transformar seus vídeos em cortes
              prontos para TikTok, Reels e Shorts — sem horas de edição.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Button asChild size="lg">
                <Link href="#planos">
                  <Zap className="h-5 w-5" />
                  Começar agora
                </Link>
              </Button>
              <Button asChild variant="secondary" size="lg">
                <Link href="#planos">
                  <Play className="h-5 w-5" />
                  Ver planos
                </Link>
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-4 text-sm text-text-secondary">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-brand" /> Acesso automático
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-brand" /> Cancele quando quiser
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-brand" /> Suporte incluído
              </span>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 rounded-3xl bg-brand-gradient opacity-20 blur-3xl" />
            <div className="relative overflow-hidden rounded-3xl border border-border bg-surface shadow-glow">
              <div className="flex items-center gap-2 border-b border-border bg-surface-elevated px-4 py-3">
                <span className="h-3 w-3 rounded-full bg-error/80" />
                <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
                <span className="h-3 w-3 rounded-full bg-success/80" />
                <span className="ml-3 text-xs text-text-secondary">forjaviral.app</span>
              </div>
              <div className="grid gap-4 p-6">
                <div className="aspect-video rounded-xl bg-gradient-to-br from-brand/30 to-surface-elevated flex items-center justify-center">
                  <Video className="h-12 w-12 text-brand-soft" />
                </div>
                <div className="space-y-2">
                  <div className="h-3 w-3/4 rounded bg-surface-elevated" />
                  <div className="h-3 w-1/2 rounded bg-surface-elevated" />
                </div>
                <div className="flex gap-2">
                  <span className="rounded-full bg-brand/15 px-2.5 py-1 text-xs text-brand-soft">Corte 1</span>
                  <span className="rounded-full bg-brand/15 px-2.5 py-1 text-xs text-brand-soft">Corte 2</span>
                  <span className="rounded-full bg-brand/15 px-2.5 py-1 text-xs text-brand-soft">Corte 3</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}