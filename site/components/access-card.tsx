'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import {
  Loader2,
  CheckCircle2,
  Copy,
  ExternalLink,
  User,
  Key,
  Clock,
  GraduationCap,
  Sparkles,
  Coins,
  PlayCircle,
  HelpCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const schema = z.object({
  email: z.string().email('E-mail inválido'),
  orderId: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export function AccessCard() {
  const searchParams = useSearchParams();
  const emailParam = searchParams.get('email') || '';
  const orderIdParam = searchParams.get('orderId') || '';

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: { email: emailParam, orderId: orderIdParam },
  });
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);

  useEffect(() => {
    if (emailParam) {
      setValue('email', emailParam);
      if (orderIdParam) setValue('orderId', orderIdParam);
      onSubmit({ email: emailParam, orderId: orderIdParam });
    }
  }, [emailParam, orderIdParam]);

  const onSubmit = async (data: FormData) => {
    setError(null);
    setResult(null);
    try {
      const params = new URLSearchParams();
      params.set('email', data.email);
      if (data.orderId) params.set('orderId', data.orderId);
      const res = await fetch(`/api/access/find?${params.toString()}`);
      const json = await res.json();
      if (!res.ok) {
        setError(json.error || 'Não encontramos acesso para esses dados.');
        return;
      }
      setResult(json);
    } catch {
      setError('Erro de conexão. Tente novamente.');
    }
  };

  const copyKey = () => {
    if (!result?.licenseKey) return;
    navigator.clipboard.writeText(result.licenseKey);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const copyAll = () => {
    if (!result) return;
    const text = `🔥 Acesso Fábrica de Cortes (fabricadecortes.com)\nChave de Licença: ${result.licenseKey}\nUsuário: ${result.username}\nCréditos: ${result.credits}\nCurso: ${result.courseUrl}\nColab: ${result.colabUrl}`;
    navigator.clipboard.writeText(text);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Recuperar seu acesso</CardTitle>
          <CardDescription>
            Informe seu e-mail de compra para visualizar sua chave de ativação, seus créditos e o link das aulas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="email">E-mail utilizado na compra</Label>
              <Input id="email" type="email" placeholder="seu@email.com" {...register('email')} />
              {errors.email && <p className="mt-1 text-xs text-error">{errors.email.message}</p>}
            </div>
            <div>
              <Label htmlFor="orderId">ID do pedido (opcional)</Label>
              <Input id="orderId" placeholder="Ex: ord_..." {...register('orderId')} />
            </div>
            {error && <p className="text-sm text-error">{error}</p>}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Buscar meu acesso'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {result && (
        <Card className="border-brand/40 bg-surface/50 shadow-2xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-brand" />
                  Seu Acesso está Liberado!
                </CardTitle>
                <CardDescription>Plano: {result.planName || 'Fábrica de Cortes'}</CardDescription>
              </div>
              <Badge variant="success">Ativo</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Chave de Licença Principal */}
            <div className="rounded-2xl border-2 border-brand/50 bg-brand/5 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-brand">
                  Sua Chave de Licença (Cole na Fábrica de Cortes)
                </span>
                <span className="flex items-center gap-1 text-xs font-semibold text-text-primary bg-surface px-2.5 py-1 rounded-full border border-border">
                  <Coins className="h-3.5 w-3.5 text-brand" /> {result.credits} Créditos
                </span>
              </div>
              <div className="flex items-center justify-between gap-3 bg-background p-3 rounded-xl border border-border">
                <code className="font-mono text-base font-bold text-text-primary select-all">
                  {result.licenseKey}
                </code>
                <Button size="sm" onClick={copyKey} variant={copiedKey ? 'secondary' : 'primary'}>
                  <Copy className="h-4 w-4 mr-1.5" />
                  {copiedKey ? 'Copiado!' : 'Copiar Chave'}
                </Button>
              </div>
              <p className="text-xs text-text-secondary">
                Insira esta chave na Fábrica de Cortes (WebUI ou Google Colab) para liberar todos os cortes automáticos com IA.
              </p>
            </div>

            {/* Grid com Curso e Google Colab */}
            <div className="grid gap-4 md:grid-cols-2">
              {/* Card Curso */}
              <div className="rounded-xl border border-border bg-background p-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-brand font-semibold text-sm">
                    <GraduationCap className="h-5 w-5" />
                    Curso & Aulas Práticas
                  </div>
                  <p className="text-xs text-text-secondary">
                    Assista ao passo a passo de como rodar a Fábrica de Cortes, gerar cortes virais e monetizar no TikTok/YouTube.
                  </p>
                </div>
                <div className="pt-4">
                  <Button asChild className="w-full" variant="secondary" size="sm">
                    <a href={result.courseUrl} target="_blank" rel="noreferrer">
                      <PlayCircle className="h-4 w-4 mr-1.5 text-brand" /> Assistir Aulas
                    </a>
                  </Button>
                </div>
              </div>

              {/* Card Google Colab */}
              <div className="rounded-xl border border-border bg-background p-4 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-brand font-semibold text-sm">
                    <ExternalLink className="h-5 w-5" />
                    Executar no Google Colab
                  </div>
                  <p className="text-xs text-text-secondary">
                    Rode nas GPUs gratuitas da nuvem do Google sem precisar de computador potente.
                  </p>
                </div>
                <div className="pt-4">
                  <Button asChild className="w-full" size="sm">
                    <a href={result.colabUrl} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-4 w-4 mr-1.5" /> Abrir no Colab
                    </a>
                  </Button>
                </div>
              </div>
            </div>

            {/* Informações da Conta */}
            <div className="rounded-xl border border-border bg-background/50 p-4 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-border/50">
                <span className="text-text-secondary">Usuário:</span>
                <span className="font-semibold text-text-primary">{result.username}</span>
              </div>
              {result.expiresAt && (
                <div className="flex justify-between py-1 border-b border-border/50">
                  <span className="text-text-secondary">Validade da Licença:</span>
                  <span className="font-semibold text-text-primary">
                    {new Date(result.expiresAt).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <Button variant="secondary" onClick={copyAll} className="w-full sm:w-auto">
                <Copy className="h-4 w-4 mr-1.5" /> {copiedAll ? 'Tudo copiado!' : 'Copiar todos os dados'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}