'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Zap, Coins, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

const PACKAGES = [
  {
    slug: 'recarga-100',
    name: '100 Créditos',
    credits: 100,
    price: 'R$ 29,90',
    cents: 2990,
    desc: 'Ideal para finalizar vídeos rápidos ou testes.',
    badge: null,
  },
  {
    slug: 'recarga-300',
    name: '300 Créditos',
    credits: 300,
    price: 'R$ 59,90',
    cents: 5990,
    desc: 'O mais escolhido. Mais de 30 vídeos virais completos.',
    badge: 'Mais Popular',
  },
  {
    slug: 'recarga-600',
    name: '600 Créditos',
    credits: 600,
    price: 'R$ 99,90',
    cents: 9990,
    desc: 'Máximo poder para agências e criadores frequentes.',
    badge: 'Melhor Custo',
  },
];

function RecargaForm() {
  const searchParams = useSearchParams();
  const [selectedPkg, setSelectedPkg] = useState('recarga-300');
  const [licenseKey, setLicenseKey] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const k = searchParams.get('key');
    if (k) setLicenseKey(k);
  }, [searchParams]);

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!licenseKey.trim()) {
      setError('Por favor, informe a sua chave de licença.');
      return;
    }
    if (!email.trim() || !name.trim()) {
      setError('Por favor, preencha seu nome e e-mail.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/checkout/recharge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          licenseKey: licenseKey.trim(),
          packageSlug: selectedPkg,
          name: name.trim(),
          email: email.trim(),
          phone: phone.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Erro ao gerar recarga.');
        return;
      }

      if (data.checkoutURL) {
        window.location.href = data.checkoutURL;
      }
    } catch {
      setError('Erro de conexão ao processar recarga.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleCheckout} className="space-y-8">
      {/* 1. Escolha do Pacote */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          1. Escolha o pacote de créditos
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          {PACKAGES.map((pkg) => {
            const isSelected = selectedPkg === pkg.slug;
            return (
              <div
                key={pkg.slug}
                onClick={() => setSelectedPkg(pkg.slug)}
                className={`cursor-pointer rounded-2xl border p-5 transition-all relative flex flex-col justify-between ${
                  isSelected
                    ? 'border-brand bg-brand/5 ring-2 ring-brand/50 shadow-lg'
                    : 'border-border bg-surface hover:border-brand/30'
                }`}
              >
                {pkg.badge && (
                  <span className="absolute -top-3 right-4 rounded-full bg-brand px-3 py-0.5 text-xs font-bold text-white shadow">
                    {pkg.badge}
                  </span>
                )}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-base text-text-primary">{pkg.name}</span>
                    <Zap className={`h-4 w-4 ${isSelected ? 'text-brand' : 'text-text-secondary'}`} />
                  </div>
                  <div className="text-2xl font-extrabold text-brand">{pkg.price}</div>
                  <p className="text-xs text-text-secondary">{pkg.desc}</p>
                </div>
                <div className="pt-4 mt-2 border-t border-border/50 flex items-center gap-1.5 text-xs font-medium text-text-primary">
                  <CheckCircle2 className="h-4 w-4 text-brand" />
                  +{pkg.credits} créditos automáticos
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Dados da Licença e Cliente */}
      <Card className="border-border bg-surface">
        <CardHeader>
          <CardTitle className="text-lg">2. Seus dados e Chave de Licença</CardTitle>
          <CardDescription>
            Informe a chave onde os créditos serão depositados automaticamente.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="licenseKey">Chave de Licença (FV-...)</Label>
            <Input
              id="licenseKey"
              placeholder="Ex: FV-ABC12-XYZ34"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
              required
              className="font-mono uppercase font-bold"
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="name">Seu Nome</Label>
              <Input
                id="name"
                placeholder="Nome completo"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="email">Seu E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor="phone">WhatsApp / Telefone (opcional para suporte)</Label>
            <Input
              id="phone"
              placeholder="(11) 99999-9999"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-error bg-error/10 p-3 rounded-xl border border-error/20">{error}</p>}

          <Button type="submit" size="lg" className="w-full text-base font-bold" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" /> Gerando Pix na AbacatePay...
              </>
            ) : (
              <>
                Recarregar Agora com Pix <ArrowRight className="h-5 w-5 ml-2" />
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </form>
  );
}

export default function RecargaPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-4xl px-4 py-16">
        <div className="text-center space-y-3 mb-12">
          <Badge variant="brand" className="mb-2">
            <Coins className="h-3.5 w-3.5 mr-1" /> Recarga Instantânea
          </Badge>
          <h1 className="font-display text-3xl md:text-4xl font-bold">
            Recarregue seus créditos do <span className="text-brand">Forja Viral</span>
          </h1>
          <p className="text-text-secondary max-w-xl mx-auto text-sm md:text-base">
            Seus créditos caem automaticamente na sua licença assim que o Pix for aprovado pela AbacatePay.
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
