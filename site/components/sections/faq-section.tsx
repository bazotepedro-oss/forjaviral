'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';

const FAQ = [
  { q: 'Como recevo acesso após a compra?', a: 'Assim que o pagamento for confirmado pela AbacatePay, nosso sistema gera automaticamente suas credenciais e link de acesso. Você recebe um e-mail e pode acessar pela página de retorno.' },
  { q: 'Preciso instalar algo no meu computador?', a: 'A ferramenta é hospedada no Railway — você acessa pelo navegador. Basta abrir o link recebido.' },
  { q: 'Posso cancelar a assinatura quando quiser?', a: 'Sim. Cancele a qualquer momento a partir do seu painel. Não há multa ou burocracia.' },
  { q: 'O que está incluído em cada plano?', a: 'Todos os planos incluem cortes com IA, legendas dinâmicas e acesso à ferramenta. Planos superiores adicão mais recursos como tradução e suporte prioritário.' },
  { q: 'E se a ferramenta parar de funcionar?', a: 'Nossa infraestrutura é monitorada 24/7. Em caso de instabilidade, entre em contato pelo suporte e receba atendimento.' },
  { q: 'Como me recupero se perder o e-mail de acesso?', a: 'Acesse /acesso e informe seu e-mail ou order ID. Se o token expirar, solicite um novo link.' },
];

export function FAQSection() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="border-b border-border">
      <div className="mx-auto w-full max-w-3xl px-4 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
            Perguntas <span className="text-brand">frequentes</span>
          </h2>
        </div>
        <div className="mt-10 space-y-3">
          {FAQ.map((item, i) => {
            const isOpen = open === i;
            return (
              <div key={i} className={cn('rounded-2xl border p-4', isOpen ? 'border-brand/40 bg-surface' : 'border-border bg-surface/60')}>
                <button
                  onClick={() => setOpen(isOpen ? null : i)}
                  className="flex w-full items-center justify-between text-left"
                >
                  <span className="font-semibold text-text-primary">{item.q}</span>
                  <span className={cn('text-xl text-brand transition-transform', isOpen ? 'rotate-45' : '')}>+</span>
                </button>
                {isOpen && <p className="mt-3 text-sm text-text-secondary">{item.a}</p>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}