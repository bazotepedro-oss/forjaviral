import Link from 'next/link';
import { Flame, Twitter, Instagram, Youtube, Mail, Github } from 'lucide-react';

const LINKS = [
  { label: 'Recursos', href: '#recursos' },
  { label: 'Como funciona', href: '#como-funcion' },
  { label: 'Planos', href: '#planos' },
  { label: 'FAQ', href: '#faq' },
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
          <div className="space-y-3">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient">
                <Flame className="h-5 w-5 text-white" />
              </div>
              <span className="font-display text-lg font-bold text-text-primary">
                Forja <span className="text-brand">Viral</span>
              </span>
            </Link>
            <p className="text-sm text-text-secondary">
              Corte vídeos longos em cortes virais com IA em segundos.
            </p>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-text-primary">Produtos</h4>
            <ul className="space-y-2">
              {LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-text-secondary hover:text-text-primary">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-text-primary">Legal</h4>
            <ul className="space-y-2">
              {LEGAL.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-text-secondary hover:text-text-primary">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-text-primary">Redes</h4>
            <div className="flex gap-3">
              {[Twitter, Instagram, Youtube, Mail, Github].map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  aria-label="Rede social"
                  className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-background text-text-secondary transition-colors hover:border-brand/50 hover:text-brand"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-8 border-t border-border pt-6 text-center text-xs text-text-secondary">
          © {new Date().getFullYear()} Forja Viral. Todos os direitos reservados.
        </div>
      </div>
    </footer>
  );
}