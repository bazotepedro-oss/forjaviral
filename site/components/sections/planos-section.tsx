import { prisma } from '@/lib/db';
import { formatPrice } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Coins, Zap, ShieldCheck } from 'lucide-react';

interface Props {
  plans: Awaited<ReturnType<typeof prisma.plan.findMany>>;
}

export function PlanosSection({ plans }: Props) {
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

        <div className="mt-14 grid gap-8 md:grid-cols-3 items-stretch">
          {plans.map((plan) => {
            const isPopular = plan.slug === 'pack_criador' || plan.slug === 'trimestral';
            const features = Array.isArray(plan.features) ? (plan.features as string[]) : [];
            
            // Cálculo do custo por vídeo
            const videoCount = plan.slug.includes('15') || plan.slug.includes('teste') ? 15 : plan.slug.includes('50') || plan.slug.includes('criador') ? 50 : 120;
            const costPerVideo = (plan.price / 100 / videoCount).toFixed(2).replace('.', ',');

            return (
              <div
                key={plan.id}
                className={cn(
                  'relative flex flex-col justify-between rounded-3xl border p-8 transition-all duration-300',
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

                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="font-display text-2xl font-bold text-text-primary">{plan.name}</h3>
                    <div className="w-8 h-8 rounded-xl bg-brand/10 flex items-center justify-center text-brand">
                      <Zap className="w-4 h-4" />
                    </div>
                  </div>

                  <div className="mt-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-5xl font-extrabold text-text-primary">
                        {formatPrice(plan.price, plan.currency)}
                      </span>
                      <span className="text-xs text-text-secondary uppercase tracking-wider font-semibold">/ pix único</span>
                    </div>
                    <div className="mt-2 text-xs text-brand font-medium">
                      Apenas R$ {costPerVideo} por corte pronto
                    </div>
                  </div>

                  <ul className="mt-8 space-y-3.5 text-left border-t border-white/5 pt-6">
                    {features.map((f, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-sm text-text-secondary">
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
                        'w-full py-3.5 px-6 rounded-xl font-bold text-sm transition-all duration-200 shadow-md',
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
                    Acesso imediato e chave no e-mail
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}