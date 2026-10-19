'use client';

import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const schema = z.object({
  slug: z.enum(['mensal', 'trimestral', 'anual']),
  name: z.string().min(2, 'Nome muito curto').max(120),
  email: z.string().email('E-mail inválido'),
  phone: z.string().max(30).optional(),
  consent: z.literal(true, { message: 'Você precisa aceitar os termos' }),
});

type FormData = z.infer<typeof schema>;

interface CheckoutFormProps {
  defaultSlug?: 'mensal' | 'trimestral' | 'anual';
}

export function CheckoutForm({ defaultSlug = 'trimestral' }: CheckoutFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { slug: defaultSlug, consent: true },
  });

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
      setToast({ message: 'Redirecionando para o checkout...', variant: 'info' });
      window.location.href = json.checkoutURL;
    } catch {
      setToast({ message: 'Erro de conexão. Tente novamente.', variant: 'error' });
    }
  };

  if (done) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <CheckCircle2 className="h-12 w-12 text-success" />
        <p className="mt-4 font-semibold text-text-primary">Checkout criado com sucesso!</p>
        <p className="text-sm text-text-secondary">Você será redirecionado em instantes...</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <form onSubmit={handleSubmit(onSubmit as Parameters<typeof handleSubmit>[0])} className="space-y-4">
        <div>
          <Label htmlFor="slug">Plano</Label>
          <select
            id="slug"
            className="mt-1 h-11 w-full rounded-xl border border-border bg-background px-4 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
            {...register('slug')}
          >
            <option value="mensal">Mensal</option>
            <option value="trimestral">Trimestral</option>
            <option value="anual">Anual</option>
          </select>
        </div>

        <div>
          <Label htmlFor="name">Nome completo</Label>
          <Input id="name" {...register('name')} />
          {errors.name && <p className="mt-1 text-xs text-error">{errors.name.message}</p>}
        </div>

        <div>
          <Label htmlFor="email">E-mail</Label>
          <Input id="email" type="email" {...register('email')} />
          {errors.email && <p className="mt-1 text-xs text-error">{errors.email.message}</p>}
        </div>

        <div>
          <Label htmlFor="phone">Telefone (opcional)</Label>
          <Input id="phone" {...register('phone')} />
        </div>

        <div className="flex items-start gap-2 pt-1">
          <input
            type="checkbox"
            id="consent"
            className="mt-1 h-4 w-4 rounded border-border bg-background accent-brand"
            {...register('consent')}
          />
          <Label htmlFor="consent" className="font-normal">
            Concordo com os{' '}
            <a href="/termos" className="text-brand hover:underline">
              termos de uso
            </a>{' '}
            e{' '}
            <a href="/privacidade" className="text-brand hover:underline">
              política de privacidade
            </a>.
          </Label>
        </div>
        {errors.consent && <p className="-mt-2 text-xs text-error">{errors.consent.message}</p>}

        <Button type="submit" className="w-full" size="lg" disabled={isSubmitting}>
          {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Ir para o checkout'}
        </Button>
      </form>

      {toast && (
        <div className="fixed bottom-4 right-4 z-50 w-full max-w-sm">
          <div className={cn('flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm shadow-card', toast.variant === 'error' ? 'border-error/30 bg-error/10 text-error' : toast.variant === 'success' ? 'border-success/30 bg-success/10 text-success' : 'border-brand/30 bg-brand/10 text-brand-soft')}>
            <span>{toast.message}</span>
            <button onClick={() => setToast(null)} className="text-current hover:opacity-70">✕</button>
          </div>
        </div>
      )}
    </div>
  );
}

import { cn } from '@/lib/utils';