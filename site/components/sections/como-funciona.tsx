import { Coins, Zap, Unlock, Headphones } from 'lucide-react';

const STEPS = [
  { icon: Coins, title: 'Escolha seu Pacote', description: 'De 15 até 250 créditos ou monte uma quantidade avulsa sob medida. Sem assinatura no cartão.' },
  { icon: Zap, title: 'Pix Instantâneo', description: 'Checkout seguro com QR Code Pix via AbacatePay e aprovação em menos de 5 segundos.' },
  { icon: Unlock, title: 'Chave e Acesso Imediatos', description: 'Nossa integração com o Railway provisiona sua licença e créditos instantaneamente na tela e no e-mail.' },
  { icon: Headphones, title: 'Corte e Viralize', description: 'Cole o link do podcast no PC ou Google Colab Nuvem e receba os cortes verticais com legendas em minutos.' },
];

export function ComoFunciona() {
  return (
    <section id="como-funciona" className="border-y border-border bg-surface">
      <div className="mx-auto w-full max-w-6xl px-4 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Como funciona em <span className="text-brand">4 passos</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
            Do Pix ao primeiro corte viral renderizado, tudo é 100% automático.
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