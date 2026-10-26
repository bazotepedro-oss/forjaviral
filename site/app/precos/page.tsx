import Link from 'next/link';
import { prisma } from '@/lib/db';
import { formatPrice, cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { Check, Coins, Zap, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const revalidate = 60;

export default async function PrecosPage() {
  const plans = await prisma.plan.findMany({ where: { active: true }, orderBy: { price: 'asc' } });

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col justify-between">
      <Navbar />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="pointer-events-none absolute inset-0 bg-brand-radial" />
          <div className="mx-auto w-full max-w-6xl px-4 py-16 text-center md:py-24">
            <Badge variant="brand" className="mb-3">
              <Coins className="h-3.5 w-3.5 mr-1" /> 1 Crédito = 1 Corte Viral Completo
            </Badge>
            <h1 className="font-display text-4xl font-extrabold tracking-tight text-text-primary md:text-5xl">
              Pacotes de Créditos. <span className="text-brand">Sem Mensalidade.</span>
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base text-text-secondary">
              Pague uma única vez via Pix. Use quando quiser: seus créditos têm validade de 1 ano inteiro e nunca expiram no fim do mês.
            </p>
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 py-16">
          <div className="grid gap-6 md:grid-cols-3">
            {plans.map((plan) => {
              const isPopular = plan.slug === 'pack_criador';
              const features = Array.isArray(plan.features) ? (plan.features as string[]) : [];
              return (
                <div
                  key={plan.id}
                  className={cn(
                    'relative flex flex-col justify-between rounded-3xl border p-7 transition-all',
                    isPopular
                      ? 'border-2 border-brand bg-brand/5 shadow-glow md:-translate-y-2'
                      : 'border-border bg-surface hover:border-brand/40'
                  )}
                >
                  {isPopular && (
                    <Badge variant="brand" className="absolute -top-3 left-1/2 -translate-x-1/2 font-bold px-3 py-0.5">
                      Mais Popular 🔥
                    </Badge>
                  )}

                  <div className="space-y-4">
                    <h3 className="font-display text-xl font-bold text-text-primary">{plan.name}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-extrabold text-text-primary">{formatPrice(plan.price, plan.currency)}</span>
                      <span className="text-xs text-text-secondary uppercase font-semibold">/ pix único</span>
                    </div>
                    <p className="text-xs text-text-secondary">Validade de 365 dias • Sem assinatura</p>

                    <ul className="mt-4 space-y-2.5 text-left border-t border-border/60 pt-4">
                      {features.map((f, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-text-secondary">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="pt-6 mt-4">
                    <Button asChild size="lg" className={cn('w-full font-bold text-sm h-11', isPopular ? 'bg-brand hover:bg-brand/90 text-white shadow-glow' : 'bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-text-primary')}>
                      <Link href={`/checkout?plan=${plan.slug}`}>
                        Comprar Pacote
                      </Link>
                    </Button>
                    <p className="mt-2 text-center text-[10px] text-text-secondary flex items-center justify-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      Liberação imediata via Pix
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-12 text-center">
            <p className="text-sm text-text-secondary">
              Já é cliente e precisa de mais créditos avulsos?{' '}
              <Link href="/recarga" className="text-brand font-semibold underline hover:text-brand/80">
                Acesse a Recarga de Créditos com desconto progressivo &rarr;
              </Link>
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}