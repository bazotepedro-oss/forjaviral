'use client';

import { useState, useEffect, Suspense, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Coins,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Sparkles,
  Zap,
  TrendingDown,
  ShieldCheck,
  QrCode,
} from 'lucide-react';

const PRESETS = [
  { credits: 50, label: '50 Vídeos', badge: 'Mais Vendido 🔥' },
  { credits: 120, label: '120 Vídeos', badge: '49% OFF' },
  { credits: 250, label: '250 Vídeos', badge: '58% OFF' },
  { credits: 1000, label: '1.000 Vídeos', badge: '70% OFF' },
  { credits: 5000, label: '5.000 Vídeos', badge: '75% OFF 🚀' },
];

function calculatePricing(credits: number) {
  const c = Math.max(5, Math.min(5000, Math.floor(credits || 5)));
  let unit = 1.30;
  let discount = 0;
  let tierLabel = 'Preço Normal';

  if (c >= 2500) {
    unit = 0.33;
    discount = 75;
    tierLabel = 'Mega Volume Industrial (75% OFF)';
  } else if (c >= 1000) {
    unit = 0.39;
    discount = 70;
    tierLabel = 'Plano Enterprise (70% OFF)';
  } else if (c >= 500) {
    unit = 0.45;
    discount = 65;
    tierLabel = 'Super Atacado (65% OFF)';
  } else if (c >= 250) {
    unit = 0.55;
    discount = 58;
    tierLabel = 'Desconto Agência (58% OFF)';
  } else if (c >= 100) {
    unit = 0.66;
    discount = 49;
    tierLabel = 'Desconto de Atacado (49% OFF)';
  } else if (c >= 50) {
    unit = 0.79;
    discount = 39;
    tierLabel = 'Super Desconto Criador (39% OFF)';
  } else if (c >= 30) {
    unit = 0.95;
    discount = 27;
    tierLabel = 'Desconto Especial (27% OFF)';
  }

  const total = c * unit;
  const normalTotal = c * 1.30;
  const economy = normalTotal - total;

  return {
    credits: c,
    unitPrice: unit,
    total,
    normalTotal,
    economy,
    discount,
    tierLabel,
  };
}

function RecargaForm() {
  const searchParams = useSearchParams();
  const [credits, setCredits] = useState<number>(50);
  const [identifier, setIdentifier] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const k = searchParams.get('key') || searchParams.get('user') || searchParams.get('email');
    if (k) setIdentifier(k);
    const c = searchParams.get('credits');
    if (c && !isNaN(Number(c))) {
      setCredits(Math.max(5, Math.min(5000, Number(c))));
    }
  }, [searchParams]);

  const pricing = useMemo(() => calculatePricing(credits), [credits]);

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!identifier.trim()) {
      setError('Por favor, informe sua Chave de Licença (FV-...), Usuário ou E-mail.');
      return;
    }
    if (!name.trim() || !email.trim()) {
      setError('Por favor, preencha seu nome e e-mail para emissão do Pix.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/checkout/recharge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier: identifier.trim(),
          credits: pricing.credits,
          name: name.trim(),
          email: email.trim(),
          phone: phone.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Erro ao gerar Pix de recarga.');
        return;
      }

      if (data.checkoutURL) {
        window.location.href = data.checkoutURL;
      }
    } catch {
      setError('Falha de conexão ao gerar recarga.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleCheckout} className="space-y-8">
      {/* 1. Escolha de Quantidade e Desconto Progressivo */}
      <Card className="border-border/80 bg-surface/90 shadow-xl backdrop-blur-sm">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <Coins className="h-5 w-5 text-brand" />
                1. Quantos créditos você quer recarregar?
              </CardTitle>
              <CardDescription>
                Cada crédito equivale a 1 corte de vídeo viral completo com legendas e renderização.
              </CardDescription>
            </div>
            <Badge variant="outline" className="border-brand/40 bg-brand/10 text-brand font-semibold px-3 py-1">
              {pricing.tierLabel}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Quick presets */}
          <div>
            <Label className="text-xs font-semibold uppercase tracking-wider text-text-secondary mb-2 block">
              Escolha rápida ou selecione abaixo:
            </Label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
              {PRESETS.map((p) => {
                const isSelected = credits === p.credits;
                return (
                  <button
                    key={p.credits}
                    type="button"
                    onClick={() => setCredits(p.credits)}
                    className={`relative rounded-xl border p-3 text-center transition-all ${
                      isSelected
                        ? 'border-brand bg-brand/15 text-text-primary ring-2 ring-brand/50 shadow-md font-bold'
                        : 'border-border bg-background/60 text-text-secondary hover:border-brand/40 hover:text-text-primary'
                    }`}
                  >
                    <div className="text-sm font-semibold">{p.label}</div>
                    <div className="mt-1 text-[11px] font-medium text-brand">{p.badge}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Slider and direct input */}
          <div className="rounded-2xl border border-border/60 bg-background/50 p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <Label htmlFor="customCredits" className="font-semibold text-text-primary">
                  Quantidade personalizada (de 5 a 5.000):
                </Label>
                <p className="text-xs text-text-secondary">Arraste a barra ou digite o número exato</p>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  id="customCredits"
                  type="number"
                  min={5}
                  max={5000}
                  value={credits}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setCredits(isNaN(val) ? 5 : Math.max(5, Math.min(5000, val)));
                  }}
                  className="w-28 text-center text-lg font-bold font-mono h-11 border-brand/40 bg-surface focus:ring-brand"
                />
                <span className="text-sm font-medium text-text-secondary">créditos</span>
              </div>
            </div>

            <input
              type="range"
              min={5}
              max={5000}
              step={5}
              value={credits}
              onChange={(e) => setCredits(Number(e.target.value))}
              className="w-full h-2.5 bg-border rounded-lg appearance-none cursor-pointer accent-brand"
            />

            {/* Discount Scale visual bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-xs">
              <div
                className={`rounded-lg p-2.5 border text-center transition-all ${
                  credits >= 50 && credits < 250
                    ? 'border-brand bg-brand/10 font-semibold text-brand'
                    : 'border-border/60 text-text-secondary'
                }`}
              >
                <div className="font-bold">50 a 249 vídeos</div>
                <div>R$ 0,79 / un (39% OFF)</div>
              </div>
              <div
                className={`rounded-lg p-2.5 border text-center transition-all ${
                  credits >= 250 && credits < 1000
                    ? 'border-brand bg-brand/10 font-semibold text-brand'
                    : 'border-border/60 text-text-secondary'
                }`}
              >
                <div className="font-bold">250 a 999 vídeos</div>
                <div>R$ 0,55 / un (58% OFF)</div>
              </div>
              <div
                className={`rounded-lg p-2.5 border text-center transition-all ${
                  credits >= 1000 && credits < 2500
                    ? 'border-brand bg-brand/10 font-semibold text-brand'
                    : 'border-border/60 text-text-secondary'
                }`}
              >
                <div className="font-bold">1.000 a 2.499 vídeos</div>
                <div>R$ 0,39 / un (70% OFF)</div>
              </div>
              <div
                className={`rounded-lg p-2.5 border text-center transition-all ${
                  credits >= 2500
                    ? 'border-brand bg-brand/10 font-semibold text-brand'
                    : 'border-border/60 text-text-secondary'
                }`}
              >
                <div className="font-bold">2.500 a 5.000 vídeos</div>
                <div>R$ 0,33 / un (75% OFF) 🚀</div>
              </div>
            </div>
          </div>

          {/* Pricing Summary Box */}
          <div className="rounded-2xl border border-brand/30 bg-gradient-to-br from-brand/10 via-surface to-surface p-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs uppercase tracking-wider font-semibold text-brand flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" /> Total do Pix a Pagar
                </span>
                <div className="flex items-baseline gap-3">
                  <span className="text-3xl sm:text-4xl font-extrabold text-text-primary">
                    {pricing.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                  {pricing.economy > 0 && (
                    <span className="text-sm line-through text-text-secondary">
                      {pricing.normalTotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </span>
                  )}
                </div>
                <p className="text-xs text-text-secondary flex items-center gap-1">
                  Equivale a{' '}
                  <strong className="text-brand">
                    {pricing.unitPrice.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </strong>{' '}
                  por vídeo completo.
                </p>
              </div>

              {pricing.economy > 0 && (
                <div className="flex items-center gap-2 rounded-xl bg-brand/15 px-4 py-2.5 border border-brand/30 text-brand text-xs font-bold">
                  <TrendingDown className="h-4 w-4" />
                  Economia de {pricing.economy.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })} ({pricing.discount}% OFF)
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Identificação da Licença e Usuário */}
      <Card className="border-border/80 bg-surface/90 shadow-xl backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-xl flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-brand" />
            2. Onde devemos creditar seus créditos?
          </CardTitle>
          <CardDescription>
            Identifique sua conta da Fábrica de Cortes. Pode ser sua chave de licença, e-mail de compra ou nome de usuário.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div>
            <Label htmlFor="identifier" className="font-semibold text-sm">
              Sua Chave de Licença (FV-...), Usuário ou E-mail cadastrado
            </Label>
            <Input
              id="identifier"
              placeholder="Ex: FV-9A1B2-C3D4E ou seu_usuario ou seu@email.com"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              className="mt-1 font-mono font-medium text-base h-11 border-border/80 bg-background/50 focus:ring-brand"
            />
            <p className="text-[12px] text-text-secondary mt-1.5">
              O sistema verifica no servidor da Railway e credita instantaneamente após a confirmação do Pix.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="name" className="text-sm">Seu Nome</Label>
              <Input
                id="name"
                placeholder="Nome completo"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="mt-1 h-10 border-border/80 bg-background/50"
              />
            </div>
            <div>
              <Label htmlFor="email" className="text-sm">Seu E-mail (para envio do comprovante)</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1 h-10 border-border/80 bg-background/50"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="phone" className="text-sm">WhatsApp / Telefone (opcional para suporte)</Label>
            <Input
              id="phone"
              placeholder="(11) 99999-9999"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="mt-1 h-10 border-border/80 bg-background/50"
            />
          </div>

          {error && (
            <div className="text-sm text-error bg-error/10 p-4 rounded-xl border border-error/20 flex items-center gap-2">
              <span className="font-bold">Aviso:</span> {error}
            </div>
          )}

          <Button
            type="submit"
            size="lg"
            className="w-full text-base font-bold h-12 shadow-lg shadow-brand/20 bg-brand hover:bg-brand/90 text-white"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" /> Gerando Pix na AbacatePay...
              </>
            ) : (
              <>
                <QrCode className="h-5 w-5 mr-2" />
                Gerar Pix de {pricing.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })} (+{pricing.credits} Créditos)
                <ArrowRight className="h-5 w-5 ml-2" />
              </>
            )}
          </Button>

          <div className="flex flex-wrap items-center justify-center gap-6 pt-2 text-xs text-text-secondary">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-brand" /> Pix com liberação automática em 5s
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-brand" /> Processado com segurança pela AbacatePay
            </span>
          </div>
        </CardContent>
      </Card>
    </form>
  );
}

export default function RecargaPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      <Navbar />
      <main className="mx-auto w-full max-w-4xl px-4 py-12 flex-1">
        <div className="text-center space-y-3 mb-10">
          <Badge variant="brand" className="mb-2">
            <Zap className="h-3.5 w-3.5 mr-1" /> Recarga Instantânea via Pix
          </Badge>
          <h1 className="font-display text-3xl sm:text-4xl font-extrabold tracking-tight">
            Recarregue seus créditos na <span className="text-brand">Fábrica de Cortes</span>
          </h1>
          <p className="text-text-secondary max-w-xl mx-auto text-sm sm:text-base">
            Desconto progressivo automático: quanto mais créditos você adicionar, mais barato fica cada vídeo cortado.
          </p>
        </div>

        <Suspense fallback={<div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />}>
          <RecargaForm />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
