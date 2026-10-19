import { prisma } from '@/lib/db';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';

export const revalidate = 0;

export default function ContatoPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Contato e <span className="text-brand">suporte</span>
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
          Precisa de ajuda? Entre em contato.
        </p>
        <div className="mt-8 space-y-4 text-text-secondary">
          <p>E-mail: <a href="mailto:contato@forjaviral.com" className="text-brand hover:underline">contato@forjaviral.com</a></p>
          <p>Discord: link placeholder</p>
          <p>Horário de atendimento: 9h às 18h (seg-sex)</p>
        </div>
      </main>
      <Footer />
    </div>
  );
}