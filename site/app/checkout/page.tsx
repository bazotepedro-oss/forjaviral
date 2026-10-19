import { prisma } from '@/lib/db';
import { formatPrice } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { CheckoutForm } from '@/components/checkout-form';

export const revalidate = 60;

export default async function CheckoutPage() {
  const plans = await prisma.plan.findMany({ where: { active: true }, orderBy: { slug: 'asc' } });

  return (
    <main className="min-h-screen">
      <section className="relative overflow-hidden border-b border-border">
        <div className="pointer-events-none absolute inset-0 bg-brand-radial" />
        <div className="mx-auto w-full max-w-6xl px-4 py-16 text-center md:py-20">
          <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Finalizar <span className="text-brand">assinatura</span>
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
            Preencha seus dados e você será redirecionado para o checkout seguro da AbacatePay.
          </p>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-12">
        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <CheckoutForm defaultSlug="trimestral" />
          </div>

          <aside>
            <div className="sticky top-24 space-y-4">
              <div className="rounded-2xl border border-border bg-surface p-6">
                <h3 className="font-display text-lg font-semibold text-text-primary">Resumo do pedido</h3>
                <div className="mt-4 space-y-3">
                  {plans.map((plan) => {
                    const features = Array.isArray(plan.features) ? (plan.features as string[]) : [];
                    const period = plan.interval === 'month' ? 'mês' : plan.interval === 'quarter' ? 'trimestre' : 'ano';
                    return (
                      <div key={plan.id} className="flex items-center justify-between rounded-xl border border-border bg-background p-3">
                        <div>
                          <p className="text-sm font-semibold text-text-primary">{plan.name}</p>
                          <p className="text-xs text-text-secondary">{features.length} recursos</p>
                        </div>
                        <Badge variant="brand">{formatPrice(plan.price, plan.currency)}/{period}</Badge>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-surface p-6">
                <h4 className="text-sm font-semibold text-text-primary">Pagamento seguro</h4>
                <ul className="mt-3 space-y-2 text-xs text-text-secondary">
                  <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> PIX e cartão</li>
                  <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> Dados nunca armazenados</li>
                  <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> Acesso imediato pós-pagamento</li>
                </ul>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}