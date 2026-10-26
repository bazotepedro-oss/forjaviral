'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Menu, X, KeyRound, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

const NAV_LINKS = [
  { label: 'Como Funciona', href: '/#como-funciona' },
  { label: 'Recursos', href: '/#recursos' },
  { label: 'Planos & Preços', href: '/#planos' },
  { label: 'Dúvidas', href: '/#faq' },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#0A0A0C]/85 backdrop-blur-xl transition-all duration-300">
      <div className="mx-auto flex h-20 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        
        {/* ── Brand Logo & Name ── */}
        <Link href="/" className="flex items-center gap-3 group shrink-0">
          <div className="relative flex items-center justify-center">
            <img
              src="/logo.png"
              alt="Fábrica de Cortes"
              className="h-10 w-10 sm:h-11 sm:w-11 rounded-xl object-contain drop-shadow-[0_0_20px_rgba(255,92,0,0.4)] transition-transform duration-300 group-hover:scale-105"
            />
          </div>
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <span className="font-display text-lg sm:text-xl font-black tracking-tight text-white">
              Fábrica de
            </span>
            <span className="font-display text-lg sm:text-xl font-black tracking-tight bg-gradient-to-r from-brand via-orange-500 to-amber-400 bg-clip-text text-transparent">
              Cortes
            </span>
          </div>
        </Link>

        {/* ── Desktop Center Navigation (Clean & Essential) ── */}
        <nav className="hidden md:flex items-center gap-1.5 lg:gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.06] backdrop-blur-md">
          {NAV_LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="px-3.5 py-1.5 text-sm font-medium text-neutral-300 hover:text-white rounded-full hover:bg-white/[0.08] transition-all duration-200 whitespace-nowrap"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* ── Desktop Right Actions (1 secondary link + 1 standout CTA) ── */}
        <div className="hidden sm:flex items-center gap-3">
          <Link
            href="/acesso"
            className="flex items-center gap-2 text-sm font-medium text-neutral-300 hover:text-white transition-colors duration-200 px-3.5 py-2 rounded-xl hover:bg-white/[0.06]"
          >
            <KeyRound className="w-4 h-4 text-brand" />
            <span className="whitespace-nowrap">Meu Acesso</span>
          </Link>

          <Link href="/#planos">
            <Button
              size="sm"
              className="h-10 px-5 rounded-xl font-bold text-sm text-white bg-gradient-to-r from-brand via-orange-500 to-amber-500 hover:brightness-110 shadow-[0_0_25px_rgba(255,92,0,0.35)] transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
            >
              <Sparkles className="w-4 h-4 mr-1.5" />
              Garantir Créditos
            </Button>
          </Link>
        </div>

        {/* ── Mobile Hamburger Button ── */}
        <div className="flex items-center gap-2 sm:hidden">
          <Link href="/#planos">
            <Button
              size="sm"
              className="h-9 px-3 rounded-lg font-bold text-xs text-white bg-gradient-to-r from-brand to-orange-500"
            >
              Créditos
            </Button>
          </Link>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 text-neutral-300 hover:text-white rounded-lg hover:bg-white/[0.06] transition-colors"
            aria-label="Menu"
          >
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* ── Mobile Dropdown Menu ── */}
      {mobileOpen && (
        <div className="border-t border-white/[0.08] bg-[#0A0A0C]/98 px-5 py-5 sm:hidden space-y-3 backdrop-blur-2xl animate-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col space-y-2">
            {NAV_LINKS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="py-2.5 text-sm font-medium text-neutral-300 hover:text-white transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </div>

          <div className="pt-3 border-t border-white/[0.08] flex flex-col gap-2.5">
            <Link
              href="/acesso"
              onClick={() => setMobileOpen(false)}
              className="flex items-center gap-2 py-2 text-sm font-semibold text-neutral-200"
            >
              <KeyRound className="w-4 h-4 text-brand" />
              <span>Meu Acesso / Chave de Licença</span>
            </Link>

            <Link href="/#planos" onClick={() => setMobileOpen(false)}>
              <Button className="w-full h-11 rounded-xl font-bold bg-gradient-to-r from-brand via-orange-500 to-amber-500 text-white shadow-lg">
                <Sparkles className="w-4 h-4 mr-2" />
                Garantir Créditos no Pix
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}