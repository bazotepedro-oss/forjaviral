import Link from 'next/link';
import { Zap, Flame } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CTAFinal() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="pointer-events-none absolute inset-0 bg-brand-radial" />
      <div className="mx-auto w-full max-w-4xl px-4 py-20 text-center">
        <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Pronto para <span className="bg-gradient-to-r from-brand to-brand-soft bg-clip-text text-transparent">viralizar</span>?
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-text-secondary">
          Comece agora e receba seu acesso em minutos.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button asChild size="lg">
            <Link href="#planos">
              <Zap className="h-5 w-5" />
              Quero meu acesso agora
            </Link>
          </Button>
          <Button asChild variant="secondary" size="lg">
            <Link href="/contato">
              <Flame className="h-5 w-5" />
              Falar com suporte
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}