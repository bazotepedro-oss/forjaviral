import { Suspense } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { CheckCircle2, ArrowRight, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { syncAbacatePay } from '@/lib/sync-abacatepay';

export const revalidate = 0;

export default async function RetornoPage() {
  // Sincroniza pagamentos da AbacatePay (v2) instantaneamente
  await syncAbacatePay().catch((e) => console.error('Erro ao sincronizar retorno:', e));

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col justify-between">
      <Navbar />
      <main className="mx-auto w-full max-w-2xl px-4 py-20 text-center flex-1 flex flex-col justify-center">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 shadow-xl">
          <CheckCircle2 className="h-10 w-10 text-emerald-400" />
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-extrabold text-text-primary">
          Pagamento <span className="text-emerald-400">Confirmado!</span>
        </h1>
        <p className="mx-auto mt-3 max-w-lg text-text-secondary text-sm sm:text-base">
          Seus créditos foram creditados diretamente no servidor da Forja Viral. Se você comprou um novo acesso, suas credenciais já estão prontas.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button asChild size="lg" className="w-full sm:w-auto font-bold bg-brand hover:bg-brand/90 text-white shadow-lg shadow-brand/20">
            <Link href="/acesso">
              <Zap className="h-4 w-4 mr-2" /> Ver Minha Licença & Acesso
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full sm:w-auto border-border">
            <Link href="/">
              Voltar ao Início <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
        </div>
      </main>
      <Footer />
    </div>
  );
}