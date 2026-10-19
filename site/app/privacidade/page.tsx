import { prisma } from '@/lib/db';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';

export const revalidate = 0;

export default function PrivacidadePage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Política de <span className="text-brand">privacidade</span>
        </h1>
        <div className="mt-8 space-y-6 text-text-secondary">
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">1. Dados coletados</h2>
            <p className="mt-2">Coletamos nome, e-mail e telefone (opcional) para processar a assinatura e enviar acesso.</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">2. Armazenamento</h2>
            <p className="mt-2">Senhas são armazenadas em hash (bcrypt). Tokens one-time são hasheados. Nunca armazenamos segredos em texto puro.</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">3. LGPD</h2>
            <p className="mt-2">Você pode solicitar remoção de dados entrando em contato. Dados de pagamento são processados pela AbacatePay.</p>
          </section>
          <section>
            <h2 className="font-display text-xl font-semibold text-text-primary">4. Contato</h2>
            <p className="mt-2">E-mail: contato@forjaviral.com (placeholder).</p>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}