import { Sparkles, Video, Subtitles, Zap, Shield, Headphones, Globe, FileVideo } from 'lucide-react';

const FEATURES = [
  { icon: Sparkles, title: 'Cortes automáticos com IA', description: 'A IA identifica os momentos mais engajantes e gera cortes prontos.' },
  { icon: Subtitles, title: 'Legendas dinâmicas', description: 'Estilo Hormozi com highlight palavra por palavra e emojis.' },
  { icon: Video, title: 'Otimizado para Reels/TikTok/Shorts', description: 'Formatos 9:16, auto-crop e legendas otimizados para cada plataforma.' },
  { icon: Zap, title: 'Processamento rápido', description: 'Transcrição com slicing: processa 1x, corta N vezes.' },
  { icon: Shield, title: 'Acesso seguro', description: 'Credenciais geradas com hash e token one-time com expiração.' },
  { icon: Headphones, title: 'Suporte', description: 'Equipe disponível para ajudar com configuração e uso.' },
  { icon: Globe, title: 'Sem complicação técnica', description: 'Instale, acesse e corte. Interface moderna e direta.' },
  { icon: FileVideo, title: 'Tradução automática', description: 'Traduza legendas para 10+ línguas automaticamente.' },
];

export function Recursos() {
  return (
    <section id="recursos" className="border-b border-border">
      <div className="mx-auto w-full max-w-6xl px-4 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Tudo o que você precisa para <span className="text-brand">viralizar</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
            Recursos profissionais em um único acesso.
          </p>
        </div>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <div key={i} className="rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-brand/40">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand/15 text-brand">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 font-display font-semibold text-text-primary">{f.title}</h3>
                <p className="mt-1.5 text-sm text-text-secondary">{f.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}