import { CheckCircle2, Rocket, CreditCard, Unlock, Headphones } from 'lucide-react';

const STEPS = [
  { icon: CreditCard, title: 'Escolha um plano', description: 'Mensal, trimestral ou anual. Escolha o que melhor se encaixa no seu ritmo.' },
  { icon: Rocket, title: 'Pague com AbacatePay', description: 'Checkout seguro via PIX ou cartão. Em minutos você confirma.' },
  { icon: Unlock, title: 'Acesso gerado automaticamente', description: 'Nossa IA provisiona suas credenciais e link de acesso instantaneamente.' },
  { icon: Headphones, title: 'Faça login e corte', description: 'Acesse a ferramenta no Railway e transforme vídeos em cortes virais.' },
];

export function ComoFunciona() {
  return (
    <section id="como-funcion" className="border-y border-border bg-surface">
      <div className="mx-auto w-full max-w-6xl px-4 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Como funciona em <span className="text-brand">4 passos</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
            Do checkout ao primeiro corte, tudo é automático.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <div key={i} className="relative rounded-2xl border border-border bg-background p-6">
                <span className="absolute -top-3 left-6 rounded-full bg-brand-gradient px-2.5 py-0.5 text-xs font-semibold text-white">
                  {i + 1}
                </span>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/15 text-brand">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mt-4 font-display text-lg font-semibold text-text-primary">{step.title}</h3>
                <p className="mt-2 text-sm text-text-secondary">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}