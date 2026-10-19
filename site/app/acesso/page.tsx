import { Suspense } from 'react';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { AccessCard } from '@/components/access-card';

export const revalidate = 0;

export default function AcessoPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20">
        <div className="text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-brand/15 text-brand">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a2 2 0 01-2 2M7 7a2 2 0 012 2m4 0a2 2 0 01-2 2m-2 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Seu <span className="text-brand">acesso</span>
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-text-secondary">
            Informe seu e-mail para recuperar suas credenciais. Se o pagamento já foi confirmado, suas credenciais estarão aqui.
          </p>
        </div>
        <div className="mt-10">
          <Suspense fallback={<div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />}>
            <AccessCard />
          </Suspense>
        </div>
      </main>
      <Footer />
    </div>
  );
}