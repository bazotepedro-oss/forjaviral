import { Quote, Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const TESTIMONIALS = [
  {
    name: 'Mateus Ramos',
    role: 'Canal Dark de Podcasts (480k no TikTok)',
    text: 'Cancelei minha conta no Opus Clip no mesmo dia que testei a Forja. Pagava R$ 160 todo mês em dólar e perdia minutos. Aqui compro 50 cortes por R$ 39 no Pix e uso quando quero.',
    highlight: 'Economia de R$ 120/mês',
  },
  {
    name: 'Lucas Vasconcelos',
    role: 'Editor de Vídeos Freelancer',
    text: 'O Face Crop e a legenda estilo Hormozi palavra por palavra são perfeitos. Só de não ter que abrir o Premiere pra sincronizar legenda na mão já me economizou 3 horas por dia de trabalho.',
    highlight: 'Retenção subiu 35%',
  },
  {
    name: 'Beatriz Castro',
    role: 'Criadora no TikTok & Reels',
    text: 'Rodo direto pelo Google Colab na nuvem porque meu notebook é fraco e não tem placa de vídeo. Não trava nada e os vídeos saem prontos em 1080p com áudio limpo. Bati 100k seguidores.',
    highlight: '100k seguidores em 60 dias',
  },
];

export function Depoimentos() {
  return (
    <section id="depoimentos" className="border-b border-border py-20 bg-surface/30">
      <div className="mx-auto w-full max-w-6xl px-4">
        <div className="text-center space-y-3 mb-12">
          <Badge variant="brand" className="mb-1">
            <Star className="h-3.5 w-3.5 mr-1 fill-brand text-brand" /> Resultados Reais
          </Badge>
          <h2 className="font-display text-3xl font-extrabold text-text-primary md:text-4xl">
            Quem produz cortes todos os dias, <span className="text-brand">recomenda</span>
          </h2>
          <p className="mx-auto max-w-xl text-text-secondary text-sm sm:text-base">
            Veja como criadores e editores de todo o Brasil estão economizando tempo e dinheiro com a Forja Viral.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((t, i) => (
            <div
              key={i}
              className="relative rounded-3xl border border-border/80 bg-surface/80 p-7 flex flex-col justify-between hover:border-brand/40 transition-all duration-300 shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex gap-1 text-yellow-400">
                    {[...Array(5)].map((_, s) => (
                      <Star key={s} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <span className="rounded-full bg-brand/10 px-2.5 py-0.5 text-[11px] font-bold text-brand border border-brand/20">
                    {t.highlight}
                  </span>
                </div>
                <Quote className="h-8 w-8 text-brand/30 mb-2" />
                <p className="text-sm leading-relaxed text-text-secondary">
                  &ldquo;{t.text}&rdquo;
                </p>
              </div>

              <div className="mt-6 pt-5 border-t border-border/50 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-gradient text-sm font-extrabold text-white shadow-md shadow-brand/20">
                  {t.name[0]}
                </div>
                <div>
                  <p className="text-sm font-bold text-text-primary">{t.name}</p>
                  <p className="text-xs text-text-secondary">{t.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}