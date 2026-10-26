'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Loader2, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const schema = z.object({
  slug: z.string({ required_error: 'Selecione um pacote' }).min(1, 'Selecione um pacote'),
  name: z.string({ required_error: 'Informe seu nome completo' }).min(2, 'Nome muito curto').max(120),
  email: z.string({ required_error: 'Informe seu e-mail' }).email('E-mail inválido'),
  phone: z.string().max(30).optional(),
  consent: z.literal(true, {
    errorMap: () => ({ message: 'Você precisa aceitar os termos' }),
  }),
});

type FormData = z.infer<typeof schema>;

interface CheckoutFormProps {
  defaultSlug?: string;
}

export function CheckoutForm({ defaultSlug = 'pack_criador' }: CheckoutFormProps) {
  const searchParams = useSearchParams();
  const planFromUrl = searchParams.get('plan') || searchParams.get('slug');

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      slug: planFromUrl || defaultSlug,
      name: '',
      email: '',
      phone: '',
      consent: true,
    },
  });

  useEffect(() => {
    if (planFromUrl) {
      setValue('slug', planFromUrl);
    }
  }, [planFromUrl, setValue]);

  const [toast, setToast] = useState<{ message: string; variant: 'success' | 'error' | 'info' } | null>(null);
  const [done, setDone] = useState(false);

  const onSubmit = async (data: FormData) => {
    setToast(null);
    try {
      const res = await fetch('/api/checkout/create-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const json = await res.json();
      if (!res.ok || !json.checkoutURL) {
        setToast({ message: json.error || 'Erro ao criar checkout', variant: 'error' });
        return;
      }
      setDone(true);
      setToast({ message: 'Redirecionando para o pagamento Pix...', variant: 'info' });
      window.location.href = json.checkoutURL;
    } catch {
      setToast({ message: 'Erro de conexão. Tente novamente.', variant: 'error' });
    }
  };

  if (done) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <CheckCircle2 className="h-12 w-12 text-success" />
        <p className="mt-4 font-semibold text-text-primary">Pedido gerado com sucesso!</p>
        <p className="text-sm text-text-secondary">Você será redirecionado para o pagamento Pix...</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit(onSubmit as Parameters<typeof handleSubmit>[0])} className="space-y-4">
        <div>
          <Label htmlFor="slug">Pacote de Créditos</Label>
          <select
            id="slug"
            className="mt-1 h-11 w-full rounded-xl border border-border bg-background px-4 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand font-medium"
            {...register('slug')}
          >
            <option value="pack_teste">Pack Teste (15 Vídeos) — R$ 19,90</option>
            <option value="pack_iniciante">Pack Iniciante (30 Vídeos) — R$ 29,90</option>
            <option value="pack_criador">Pack Criador (50 Vídeos) — R$ 39,90 [Mais Popular 🔥]</option>
            <option value="pack_escala">Pack Escala (120 Vídeos) — R$ 79,90 [Melhor Custo]</option>
            <option value="pack_pro">Pack Agência / Pro (250 Vídeos) — R$ 139,90</option>
          </select>
        </div>

        <div>
          <Label htmlFor="name">Seu Nome</Label>
          <Input id="name" placeholder="Ex: Lucas Silva" {...register('name')} />
          {errors.name && <p className="mt-1 text-xs text-error">{errors.name.message}</p>}
        </div>

        <div>
          <Label htmlFor="email">E-mail (onde receberá a chave e o curso)</Label>
          <Input id="email" type="email" placeholder="Ex: lucas@gmail.com" {...register('email')} />
          {errors.email && <p className="mt-1 text-xs text-error">{errors.email.message}</p>}
        </div>

        <div>
          <Label htmlFor="phone">WhatsApp / Telefone (para suporte do CRM)</Label>
          <Input id="phone" placeholder="Ex: 11999999999" {...register('phone')} />
        </div>

        <div className="flex items-start gap-2 pt-1">
          <input
            type="checkbox"
            id="consent"
            className="mt-1 h-4 w-4 rounded border-border bg-background accent-brand"
            {...register('consent')}
          />
          <Label htmlFor="consent" className="font-normal text-xs text-text-secondary">
            Concordo com os <a href="/termos" className="text-brand hover:underline">termos de uso</a>. Compreendo que este é um pagamento único de créditos pré-pagos sem cobrança recorrente no cartão.
          </Label>
        </div>
        {errors.consent && <p className="mt-1 text-xs text-error">{errors.consent.message}</p>}

        <Button type="submit" className="w-full bg-brand-gradient hover:brightness-110 shadow-glow font-bold py-3 text-base" disabled={isSubmitting}>
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Gerando Pix...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Zap className="h-4 w-4" /> Finalizar Pedido no Pix
            </span>
          )}
        </Button>
      </form>

      {toast && (
        <div className={`mt-4 p-3 rounded-xl text-xs font-semibold ${toast.variant === 'error' ? 'bg-rose-500/15 border border-rose-500/30 text-rose-400' : 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-400'}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}