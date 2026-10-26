'use client';

import { useState } from 'react';
import { Loader2, Eye, EyeOff, ShieldCheck, KeyRound } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Toast } from '@/components/ui/toast';

export default function AdminLoginPage() {
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<{ message: string; variant: 'success' | 'error' | 'info' } | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setToast(null);

    if (!password.trim()) {
      setToast({ message: 'Digite a senha ou token de admin', variant: 'error' });
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          password: password.trim(),
          email: email.trim() || undefined,
        }),
        credentials: 'include',
      });

      if (!res.ok) {
        setToast({ message: 'Senha ou Token de admin inválido', variant: 'error' });
        return;
      }

      setToast({ message: 'Acesso autorizado! Redirecionando...', variant: 'success' });
      window.location.href = '/admin';
    } catch {
      setToast({ message: 'Erro de conexão com o servidor', variant: 'error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md border-border/80 bg-surface/90 shadow-2xl backdrop-blur-md">
        <CardHeader className="text-center">
          <img
            src="/logo.png"
            alt="Fábrica de Cortes"
            className="mx-auto mb-3 h-14 w-14 rounded-2xl object-contain shadow-xl shadow-brand/20"
          />
          <CardTitle className="text-2xl font-bold">Painel Fábrica de Cortes</CardTitle>
          <CardDescription>
            Área restrita. Digite sua senha para acessar o painel de gerenciamento.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-5">
            <div>
              <Label htmlFor="password" className="text-sm font-semibold flex items-center gap-1.5">
                <KeyRound className="h-4 w-4 text-brand" />
                Senha de Administrador
              </Label>
              <div className="relative mt-1">
                <Input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pr-10 h-11 border-border/80 bg-background/50 text-base"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
                  aria-label="Mostrar senha"
                >
                  {showPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {showAdvanced && (
              <div>
                <Label htmlFor="email" className="text-xs text-text-secondary">E-mail administrativo (opcional)</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="admin@fabricadecortes.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 h-9 border-border/80 bg-background/50 text-xs"
                />
              </div>
            )}

            <div className="flex justify-between items-center text-xs">
              <button
                type="button"
                onClick={() => setShowAdvanced((v) => !v)}
                className="text-text-secondary hover:text-brand underline"
              >
                {showAdvanced ? 'Ocultar e-mail' : 'Opções avançadas'}
              </button>
            </div>

            <Button
              type="submit"
              className="w-full h-11 text-base font-bold bg-brand hover:bg-brand/90 text-white shadow-lg shadow-brand/20"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" /> Entrando...
                </>
              ) : (
                'Entrar no Painel'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {toast && (
        <div className="fixed bottom-4 right-4 z-50 w-full max-w-sm">
          <Toast message={toast.message} variant={toast.variant} onDismiss={() => setToast(null)} />
        </div>
      )}
    </div>
  );
}