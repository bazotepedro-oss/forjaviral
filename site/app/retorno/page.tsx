import { Suspense } from 'react';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';

export const revalidate = 0;

export default function RetornoPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-brand/15 text-brand">
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Processando seu <span className="text-brand">pagamento</span>
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-text-secondary">
          Aguardando confirmação da AbacatePay. Assim que aprovado, seu acesso será gerado automaticamente.
        </p>
        <div className="mt-8 space-y-4">
          <div className="mx-auto h-2 w-48 overflow-hidden rounded-full bg-surface">
            <div className="h-full w-1/3 animate-pulse bg-brand-gradient" />
          </div>
          <div className="pt-4">
            <a
              href="/acesso"
              className="inline-flex items-center justify-center rounded-xl bg-brand px-6 py-3 text-sm font-bold text-white hover:bg-brand/90 transition-all shadow-lg shadow-brand/20"
            >
              Ver minhas credenciais e aulas →
            </a>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}