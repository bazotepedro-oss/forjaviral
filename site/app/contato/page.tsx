import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { Mail, MessageSquare, Clock, Headphones } from 'lucide-react';

export const revalidate = 0;

export default function ContatoPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col justify-between">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20 flex-1">
        <div className="text-center">
          <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand/15 text-brand border border-brand/30">
            <Headphones className="h-7 w-7" />
          </div>
          <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Contato e <span className="text-brand">Suporte Oficial</span>
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-text-secondary text-sm sm:text-base">
            Dúvidas sobre sua licença, ativação no Google Colab ou sugestões? Fale diretamente com o nosso time.
          </p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-border bg-surface p-6 space-y-3">
            <div className="flex items-center gap-2 text-brand font-bold text-sm">
              <Mail className="h-4 w-4" /> E-mail de Suporte
            </div>
            <p className="text-xs text-text-secondary">
              Para dúvidas sobre pagamentos, notas ou parcerias comerciais:
            </p>
            <p className="font-semibold text-text-primary text-sm">
              <a href="mailto:contato@fabricadecortes.com" className="text-brand hover:underline">
                contato@fabricadecortes.com
              </a>
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-6 space-y-3">
            <div className="flex items-center gap-2 text-brand font-bold text-sm">
              <MessageSquare className="h-4 w-4" /> Comunidade no Discord
            </div>
            <p className="text-xs text-text-secondary">
              Tire dúvidas rápidas e troque ideias com outros criadores de conteúdo:
            </p>
            <p className="font-semibold text-text-primary text-sm">
              <a
                href="https://discord.gg/tAdPHFAbud"
                target="_blank"
                rel="noreferrer"
                className="text-brand hover:underline inline-flex items-center gap-1"
              >
                discord.gg/tAdPHFAbud &rarr;
              </a>
            </p>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-border bg-background p-4 flex items-center gap-3 text-xs text-text-secondary">
          <Clock className="h-4 w-4 text-brand shrink-0" />
          <span>Atendimento de segunda a sexta, das 09h às 18h (Horário de Brasília).</span>
        </div>
      </main>
      <Footer />
    </div>
  );
}