import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-brand/10 border border-brand/20 flex items-center justify-center mb-6">
        <span className="text-3xl font-black text-brand">404</span>
      </div>
      <h1 className="text-3xl font-bold text-white mb-2">Página Não Encontrada</h1>
      <p className="text-text-secondary max-w-md mb-8 text-sm">
        O link que você tentou acessar não existe ou foi movido na Fábrica de Cortes.
      </p>
      <Link href="/">
        <Button className="bg-brand hover:bg-brand/90 text-white font-semibold px-6 py-2.5 rounded-xl shadow-lg shadow-brand/20">
          Voltar para a Página Inicial
        </Button>
      </Link>
    </div>
  );
}
