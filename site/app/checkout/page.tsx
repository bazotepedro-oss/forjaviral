import { Suspense } from 'react';
import { prisma } from '@/lib/db';
import { formatPrice } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { CheckoutForm } from '@/components/checkout-form';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { ShieldCheck, Zap, Coins } from 'lucide-react';

export const revalidate = 60;

interface CheckoutPageProps {
  searchParams?: { plan?: string; slug?: string };
}

export default async function CheckoutPage({ searchParams }: CheckoutPageProps) {
  const plans = await prisma.plan.findMany({ where: { active: true }, orderBy: { price: 'asc' } });
  const defaultSlug = searchParams?.plan || searchParams?.slug || 'pack_criador';

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col justify-between">
      <Navbar />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-border">
          <div className="pointer-events-none absolute inset-0 bg-brand-radial" />
          <div className="mx-auto w-full max-w-6xl px-4 py-14 text-center md:py-18">
            <Badge variant="brand" className="mb-3">
              <Zap className="h-3.5 w-3.5 mr-1" /> Checkout Rápido & Seguro
            </Badge>
            <h1 className="font-display text-3xl font-extrabold text-text-primary md:text-4xl">
              Liberar Meu <span className="text-brand">Acesso Imediato</span>
            </h1>
            <p className="mx-auto mt-3 max-w-xl text-text-secondary text-sm sm:text-base">
              Preencha seus dados abaixo para gerar seu Pix. Sua chave de licença oficial e os créditos serão ativados em menos de 5 segundos.
            </p>
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 py-12">
          <div className="grid gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Suspense fallback={<div className="h-96 rounded-2xl border border-border bg-surface animate-pulse" />}>
                <CheckoutForm defaultSlug={defaultSlug} />
              </Suspense>
            </div>

            <aside>
              <div className="sticky top-24 space-y-4">
                <div className="rounded-2xl border border-border bg-surface p-6 shadow-xl">
                  <h3 className="font-display text-lg font-bold text-text-primary flex items-center gap-2">
                    <Coins className="h-5 w-5 text-brand" /> Pacotes de Créditos
                  </h3>
                  <p className="text-xs text-text-secondary mt-1">1 crédito = 1 corte viral completo com IA e legendas</p>

                  <div className="mt-4 space-y-2.5">
                    {plans.map((plan) => {
                      const features = Array.isArray(plan.features) ? (plan.features as string[]) : [];
                      return (
                        <div key={plan.id} className="flex items-center justify-between rounded-xl border border-border bg-background p-3 text-xs">
                          <div>
                            <p className="font-bold text-text-primary">{plan.name}</p>
                            <p className="text-[11px] text-text-secondary">Validade: 365 dias (Sem mensalidade)</p>
                          </div>
                          <Badge variant="brand">{formatPrice(plan.price, plan.currency)}</Badge>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-surface p-6">
                  <h4 className="text-sm font-bold text-text-primary flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" /> Garantia & Segurança
                  </h4>
                  <ul className="mt-3 space-y-2 text-xs text-text-secondary">
                    <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> Pagamento instantâneo via Pix (AbacatePay)</li>
                    <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> Chave gerada na hora na tela e no e-mail</li>
                    <li className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-brand" /> Acesso ao curso e tutoriais passo a passo</li>
                  </ul>
                </div>
              </div>
            </aside>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}