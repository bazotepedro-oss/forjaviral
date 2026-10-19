import { prisma } from '@/lib/db';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';

export const revalidate = 0;

export default function TermosPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Termos de <span className="text-brand">uso</span>
        </h1>
        <div className="mt-8 space-y-6 text-text-secondary">
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">1. Aceitação dos termos</h2>
            <p className="mt-2">Ao assinar a Forja Viral, você concorda com estes termos de uso.</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">2. Assinatura</h2>
            <p className="mt-2">Planos mensal, trimestral ou anual. Cancele a qualquer momento. Preços editáveis no painel admin.</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">3. Uso da ferramenta</h2>
            <p className="mt-2">A ferramenta é usada para cortes de vídeo com IA. É proibido uso ilegal ou que viole direitos de terceiros.</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">4. Cancelamento</h2>
            <p className="mt-2">Ao cancelar, o acesso é revogado e a assinatura é suspensa.</p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}