import { Quote } from 'lucide-react';

const TESTIMONIALS = [
  { name: 'Maria S.', role: 'Criadora de Conteúdo', text: 'Editava 4 horas por vídeo. Com a Forja Viral faço 5 cortes em 20 minutos. Mudou minha produtividade.' },
  { name: 'João P.', role: 'Editor Freelancer', text: 'A IA acerta os ganchos. Minha taxa de retenção subiu 30% desde que comecei a usar.' },
  { name: 'Ana L.', role: 'Product Maker', text: 'Acesso automático após o pagamento — sem waiting list, sem complicações. Experiência impecável.' },
];

export function Depoimentos() {
  return (
    <section id="depoimentos" className="border-y border-border bg-surface">
      <div className="mx-auto w-full max-w-6xl px-4 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Quem usa, <span className="text-brand">recomenda</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
            Depoimentos de criadores que transformaram seu fluxo de trabalho.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <div key={i} className="relative rounded-2xl border border-border bg-background p-6">
              <Quote className="h-8 w-8 text-brand/40" />
              <p className="mt-3 text-text-secondary">&ldquo;{t.text}&rdquo;</p>
              <div className="mt-6 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-gradient text-sm font-bold text-white">
                  {t.name[0]}
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">{t.name}</p>
                  <p className="text-xs text-text-secondary">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-6 text-center text-xs text-text-secondary">
          * Exemplos editáveis para demonstração.
        </p>
      </div>
    </section>
  );
}