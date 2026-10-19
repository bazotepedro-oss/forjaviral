import { prisma } from '@/lib/db';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';

export const revalidate = 0;

export default function SuportePage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Central de <span className="text-brand">suporte</span>
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-text-secondary">
          Aqui você encontra ajuda para configurar e usar a Forja Viral.
        </p>
        <div className="mt-8 space-y-4 text-text-secondary">
          <p>1. Acesse /acesso com seu e-mail para ver credenciais.</p>
          <p>2. Clique em &ldquo;Abrir ferramenta&rdquo; para ir para o app no Railway.</p>
          <p>3. Se o acesso expirou, solicite um novo link.</p>
        </div>
      </main>
      <Footer />
    </div>
  );
}