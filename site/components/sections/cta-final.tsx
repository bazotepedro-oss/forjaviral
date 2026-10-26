import Link from 'next/link';
import { Zap, Sliders, ShieldCheck, Flame, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CTAFinal() {
  return (
    <section className="relative overflow-hidden border-b border-border py-20 bg-surface/50">
      <div className="pointer-events-none absolute inset-0 bg-brand-radial" />
      <div className="pointer-events-none absolute -bottom-20 left-1/2 -translate-x-1/2 h-72 w-96 rounded-full bg-brand/15 blur-3xl" />

      <div className="relative mx-auto w-full max-w-4xl px-4 text-center space-y-6">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-3.5 py-1 text-xs font-semibold text-brand">
          <Flame className="w-3.5 h-3.5" />
          Acesso Imediato via Pix
        </div>

        <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold text-text-primary tracking-tight">
          Pronto para produzir seus primeiros{' '}
          <span className="bg-gradient-to-r from-brand via-brand-soft to-orange-400 bg-clip-text text-transparent">
            cortes virais
          </span>
          ?
        </h2>

        <p className="mx-auto max-w-xl text-base text-text-secondary leading-relaxed">
          Sem assinaturas presas no cartão. Pague apenas pelos vídeos que produzir a partir de R$ 19,90 e receba sua licença em 5 segundos.
        </p>

        <div className="pt-2 flex flex-col sm:flex-row justify-center items-center gap-3.5">
          <Button asChild size="lg" className="w-full sm:w-auto font-bold h-12 px-8 bg-brand-gradient hover:brightness-110 text-white shadow-lg shadow-brand/20">
            <Link href="#planos">
              <Zap className="h-5 w-5 mr-2" />
              Garantir Créditos Agora
              <ArrowRight className="h-5 w-5 ml-2" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full sm:w-auto font-semibold h-12 px-6 border-border hover:bg-surface-elevated">
            <Link href="/recarga">
              <Sliders className="h-4 w-4 mr-2 text-brand" />
              Já sou cliente / Recarregar
            </Link>
          </Button>
        </div>

        <p className="text-xs text-text-secondary flex items-center justify-center gap-1.5 pt-2">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          Garantia incondicional de 7 dias ou seu dinheiro de volta.
        </p>
      </div>
    </section>
  );
}