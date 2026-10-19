import { prisma } from '@/lib/db';
import { formatPrice } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface Props {
  plans: Awaited<ReturnType<typeof prisma.plan.findMany>>;
}

export function PlanosSection({ plans }: Props) {
  return (
    <section id="planos" className="border-b border-border">
      <div className="mx-auto w-full max-w-6xl px-4 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Planos <span className="text-brand">simples</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
            Escolha o ritmo do seu conteúdo. Cancele quando quiser.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {plans.map((plan) => {
            const isPopular = plan.slug === 'trimestral';
            const features = Array.isArray(plan.features) ? (plan.features as string[]) : [];
            const period = plan.interval === 'month' ? 'mês' : plan.interval === 'quarter' ? 'trimestre' : 'ano';
            return (
              <div
                key={plan.id}
                className={cn(
                  'relative flex flex-col rounded-2xl border p-6 transition-all',
                  isPopular ? 'border-brand bg-brand/5 shadow-glow' : 'border-border bg-surface hover:border-white/20'
                )}
              >
                {isPopular && (
                  <Badge variant="brand" className="absolute -top-3 left-1/2 -translate-x-1/2">
                    Mais popular
                  </Badge>
                )}
                <h3 className="font-display text-xl font-bold text-text-primary">{plan.name}</h3>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-text-primary">{formatPrice(plan.price, plan.currency)}</span>
                  <span className="text-sm text-text-secondary">/{period}</span>
                </div>
                <a href="#checkout" className="mt-6 block">
                  <span className={cn('inline-flex w-full items-center justify-center rounded-xl py-3 text-sm font-semibold', isPopular ? 'bg-brand-gradient text-white shadow-glow' : 'border border-white/10 bg-surface text-text-primary hover:border-brand/50')}>
                    Assinar
                  </span>
                </a>
                <ul className="mt-6 space-y-3 text-left">
                  {features.map((f, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-text-secondary">
                      <span className="mt-1 h-4 w-4 shrink-0 text-brand">✓</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}