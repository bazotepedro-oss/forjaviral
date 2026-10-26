import Link from 'next/link';
import { Flame, Mail } from 'lucide-react';

const LINKS = [
  { label: 'Recursos', href: '/#recursos' },
  { label: 'Como funciona', href: '/#como-funciona' },
  { label: 'Planos & Preços', href: '/#planos' },
  { label: 'Recarregar Créditos', href: '/recarga' },
  { label: 'Recuperar Meu Acesso', href: '/acesso' },
  { label: 'Dúvidas Frequentes', href: '/#faq' },
];

const LEGAL = [
  { label: 'Termos de uso', href: '/termos' },
  { label: 'Privacidade', href: '/privacidade' },
  { label: 'Contato', href: '/contato' },
  { label: 'Suporte', href: '/suporte' },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto w-full max-w-6xl px-4 py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="space-y-3 md:col-span-2">
            <Link href="/" className="flex items-center gap-2.5 group">
              <img
                src="/logo.png"
                alt="Fábrica de Cortes"
                className="h-9 w-9 rounded-xl object-contain shadow-[0_0_15px_rgba(255,92,0,0.3)] group-hover:scale-105 transition-transform"
              />
              <span className="font-display text-lg font-bold text-text-primary">
                Fábrica de <span className="text-brand">Cortes</span>
              </span>
            </Link>
            <p className="text-sm text-text-secondary max-w-sm">
              Corte vídeos longos em virais com IA em segundos. Legendas dinâmicas estilo TikTok e enquadramento automático de rostos no <span className="text-brand font-semibold">fabricadecortes.com</span>.
            </p>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-text-primary">Acesso & Produtos</h4>
            <ul className="space-y-2">
              {LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-text-primary">Ajuda & Legal</h4>
            <ul className="space-y-2">
              {LEGAL.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-text-secondary hover:text-text-primary transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-border pt-6 text-center text-xs text-text-secondary">
          © {new Date().getFullYear()} Fábrica de Cortes (<a href="https://fabricadecortes.com" className="text-brand hover:underline">fabricadecortes.com</a>). Todos os direitos reservados.
        </div>
      </div>
    </footer>
  );
}