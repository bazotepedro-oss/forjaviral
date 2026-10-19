'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { HelpCircle } from 'lucide-react';

const FAQ = [
  {
    q: 'Como funciona o sistema de créditos? Tem alguma mensalidade?',
    a: 'NÃO cobramos nenhuma mensalidade e não prendemos seu cartão de crédito! Você compra apenas os créditos que desejar via Pix (1 crédito = 1 corte viral completo com legenda dinâmica e face crop). Seus créditos ficam salvos na sua chave e nunca são apagados no fim do mês.',
  },
  {
    q: 'Quanto tempo duram os créditos após a compra?',
    a: 'Todos os pacotes de créditos têm validade de 365 dias (1 ano inteiro). Você pode usar 5 vídeos hoje, 10 mês que vem e o restante quando quiser. Nada expira às pressas.',
  },
  {
    q: 'Preciso ter um computador potente com placa de vídeo?',
    a: 'Não é obrigatório! A Forja Viral funciona de duas formas: (1) Se você tiver PC com placa NVIDIA, roda com aceleração máxima de GPU localmente. (2) Se tiver um PC fraco ou notebook comum, você roda diretamente na nuvem pelo Google Colab gratuito, sem gastar nem esquentar seu computador.',
  },
  {
    q: 'Como recebo minha chave de licença após o pagamento?',
    a: 'Assim que o Pix for aprovado pela AbacatePay (geralmente em menos de 5 segundos), você é redirecionado para a tela de acesso com sua chave FV-XXXXX gerada na hora, além de receber uma cópia no seu e-mail cadastrado.',
  },
  {
    q: 'Como funciona a recarga de créditos se os meus acabarem?',
    a: 'Basta acessar a página de Recarga (/recarga), informar sua chave FV-... ou e-mail, escolher quantos créditos quer adicionar e pagar o Pix. O servidor da Railway injeta os novos créditos na sua licença automaticamente em segundos.',
  },
  {
    q: 'Posso exportar o projeto para o Premiere Pro ou DaVinci Resolve?',
    a: 'Sim! Além de renderizar o vídeo final em MP4 1080p pronto para postar no TikTok/Reels, a Forja Viral gera arquivos XML de timeline aberta para você ajustar cores, trilha ou efeitos no Adobe Premiere ou DaVinci.',
  },
];

export function FAQSection() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="border-b border-border py-20 relative">
      <div className="mx-auto w-full max-w-3xl px-4">
        <div className="text-center space-y-3 mb-10">
          <Badge variant="brand" className="mb-1">
            <HelpCircle className="h-3.5 w-3.5 mr-1" /> Dúvidas Frequentes
          </Badge>
          <h2 className="font-display text-3xl font-extrabold text-text-primary md:text-4xl">
            Tire todas as suas <span className="text-brand">dúvidas</span>
          </h2>
          <p className="text-sm sm:text-base text-text-secondary max-w-xl mx-auto">
            Tudo o que você precisa saber sobre o modelo de créditos, entrega instantânea e funcionamento da IA.
          </p>
        </div>

        <div className="space-y-3">
          {FAQ.map((item, i) => {
            const isOpen = open === i;
            return (
              <div
                key={i}
                className={cn(
                  'rounded-2xl border transition-all duration-200',
                  isOpen
                    ? 'border-brand/50 bg-surface shadow-lg ring-1 ring-brand/30'
                    : 'border-border/80 bg-surface/60 hover:border-brand/30'
                )}
              >
                <button
                  onClick={() => setOpen(isOpen ? null : i)}
                  className="flex w-full items-center justify-between p-5 text-left font-semibold text-text-primary text-sm sm:text-base"
                >
                  <span>{item.q}</span>
                  <span
                    className={cn(
                      'ml-4 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-surface-elevated text-sm text-brand transition-transform duration-200',
                      isOpen && 'rotate-45 bg-brand text-white'
                    )}
                  >
                    +
                  </span>
                </button>
                {isOpen && (
                  <div className="px-5 pb-5 text-sm leading-relaxed text-text-secondary border-t border-border/50 pt-3">
                    {item.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}