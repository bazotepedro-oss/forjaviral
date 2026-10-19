'use client';

import { useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { cn, formatPrice } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ShoppingCart,
  RefreshCcw,
  Users,
  Key,
  Webhook,
  LogOut,
  ChevronRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  RotateCcw,
  ShieldOff,
  Zap,
  Activity,
  MessageCircle,
  Copy,
  PlusCircle,
  Search,
} from 'lucide-react';

// ── Types (mirrored from Prisma) ──────────────────────────────────────────────

interface Plan {
  id: string;
  name: string;
  slug: string;
  price: number;
  currency: string;
  interval: string;
}

interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  createdAt: Date | string;
  orders?: any[];
  credentials?: {
    id: string;
    username: string;
    licenseKey?: string | null;
    credits?: number | null;
    status: string;
    expiresAt?: Date | string | null;
  }[];
}

interface Order {
  id: string;
  status: string;
  amount: number;
  currency: string;
  createdAt: Date | string;
  paidAt?: Date | string | null;
  customer: Customer;
  plan: Plan;
}

interface Subscription {
  id: string;
  status: string;
  provider: string;
  currentPeriodEnd?: Date | string | null;
  createdAt: Date | string;
  customer: Customer;
  plan: Plan;
}

interface Credential {
  id: string;
  username: string;
  accessUrl: string;
  railwayAppUrl?: string | null;
  licenseKey?: string | null;
  credits?: number | null;
  status: string;
  expiresAt?: Date | string | null;
  createdAt: Date | string;
  customer: Customer;
  order?: { id: string } | null;
}

interface WebhookEvent {
  id: string;
  provider: string;
  eventId: string;
  type: string;
  processed: boolean;
  createdAt: Date | string;
  orderId?: string | null;
}

interface AdminShellProps {
  orders: Order[];
  subscriptions: Subscription[];
  customers: Customer[];
  credentials: Credential[];
  events: WebhookEvent[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const fmt = (d: Date | string | null | undefined) =>
  d ? new Date(d).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '—';

const statusColor: Record<string, 'success' | 'brand' | 'default' | 'outline'> = {
  paid: 'success',
  active: 'success',
  completed: 'success',
  pending: 'brand',
  processing: 'brand',
  cancelled: 'outline',
  expired: 'outline',
  revoked: 'outline',
  failed: 'outline',
};

const statusLabel: Record<string, string> = {
  paid: 'Pago',
  active: 'Ativo',
  completed: 'Concluído',
  pending: 'Pendente',
  processing: 'Processando',
  cancelled: 'Cancelado',
  expired: 'Expirado',
  revoked: 'Revogado',
  failed: 'Falhou',
};

function StatusBadge({ status }: { status: string }) {
  const variant = statusColor[status] ?? 'default';
  return <Badge variant={variant}>{statusLabel[status] ?? status}</Badge>;
}

// ── Tab config ────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'orders',        label: 'Pedidos',         Icon: ShoppingCart },
  { id: 'subscriptions', label: 'Assinaturas',     Icon: RefreshCcw   },
  { id: 'customers',     label: 'CRM & WhatsApp',  Icon: Users        },
  { id: 'credentials',   label: 'Credenciais',     Icon: Key          },
  { id: 'events',        label: 'Webhooks',        Icon: Webhook      },
] as const;

type TabId = (typeof TABS)[number]['id'];

// ── Sub-panels ────────────────────────────────────────────────────────────────

function OrdersPanel({ orders }: { orders: Order[] }) {
  const router = useRouter();
  const [, startTransition] = useTransition();
  const [activating, setActivating] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ id: string; text: string; ok: boolean } | null>(null);

  async function activate(orderId: string) {
    setActivating(orderId);
    setMsg(null);
    try {
      const res = await fetch(`/api/admin/orders/${orderId}/activate`, { method: 'POST' });
      const data = await res.json();
      setMsg({ id: orderId, text: data.message ?? (res.ok ? 'Ativado' : 'Erro'), ok: res.ok });
      if (res.ok) startTransition(() => router.refresh());
    } catch {
      setMsg({ id: orderId, text: 'Erro de rede', ok: false });
    } finally {
      setActivating(null);
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-text-secondary text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-4 font-medium">ID</th>
            <th className="text-left py-3 px-4 font-medium">Cliente</th>
            <th className="text-left py-3 px-4 font-medium">Plano</th>
            <th className="text-left py-3 px-4 font-medium">Valor</th>
            <th className="text-left py-3 px-4 font-medium">Status</th>
            <th className="text-left py-3 px-4 font-medium">Criado</th>
            <th className="text-left py-3 px-4 font-medium">Pago em</th>
            <th className="text-left py-3 px-4 font-medium">Ações</th>
          </tr>
        </thead>
        <tbody>
          {orders.length === 0 && (
            <tr>
              <td colSpan={8} className="py-12 text-center text-text-secondary">Nenhum pedido ainda.</td>
            </tr>
          )}
          {orders.map((o) => (
            <tr key={o.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td className="py-3 px-4 font-mono text-xs text-text-secondary">{o.id.slice(-8)}</td>
              <td className="py-3 px-4">
                <div className="font-medium text-text-primary">{o.customer.name}</div>
                <div className="text-xs text-text-secondary">{o.customer.email}</div>
              </td>
              <td className="py-3 px-4 text-text-secondary">{o.plan.name}</td>
              <td className="py-3 px-4 font-semibold">{formatPrice(o.amount, o.currency)}</td>
              <td className="py-3 px-4"><StatusBadge status={o.status} /></td>
              <td className="py-3 px-4 text-text-secondary text-xs">{fmt(o.createdAt)}</td>
              <td className="py-3 px-4 text-text-secondary text-xs">{fmt(o.paidAt)}</td>
              <td className="py-3 px-4">
                {o.status === 'pending' && (
                  <div className="flex flex-col gap-1">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={activating === o.id}
                      onClick={() => activate(o.id)}
                      className="text-xs"
                    >
                      <Zap className="w-3 h-3" />
                      {activating === o.id ? 'Ativando…' : 'Ativar manual'}
                    </Button>
                    {msg?.id === o.id && (
                      <span className={cn('text-xs', msg.ok ? 'text-success' : 'text-error')}>
                        {msg.text}
                      </span>
                    )}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SubscriptionsPanel({ subscriptions }: { subscriptions: Subscription[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-text-secondary text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-4 font-medium">ID</th>
            <th className="text-left py-3 px-4 font-medium">Cliente</th>
            <th className="text-left py-3 px-4 font-medium">Plano</th>
            <th className="text-left py-3 px-4 font-medium">Provedor</th>
            <th className="text-left py-3 px-4 font-medium">Status</th>
            <th className="text-left py-3 px-4 font-medium">Próx. renovação</th>
            <th className="text-left py-3 px-4 font-medium">Criado</th>
          </tr>
        </thead>
        <tbody>
          {subscriptions.length === 0 && (
            <tr>
              <td colSpan={7} className="py-12 text-center text-text-secondary">Nenhuma assinatura ainda.</td>
            </tr>
          )}
          {subscriptions.map((s) => (
            <tr key={s.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td className="py-3 px-4 font-mono text-xs text-text-secondary">{s.id.slice(-8)}</td>
              <td className="py-3 px-4">
                <div className="font-medium text-text-primary">{s.customer.name}</div>
                <div className="text-xs text-text-secondary">{s.customer.email}</div>
              </td>
              <td className="py-3 px-4 text-text-secondary">{s.plan.name}</td>
              <td className="py-3 px-4 text-text-secondary">{s.provider}</td>
              <td className="py-3 px-4"><StatusBadge status={s.status} /></td>
              <td className="py-3 px-4 text-text-secondary text-xs">{fmt(s.currentPeriodEnd)}</td>
              <td className="py-3 px-4 text-text-secondary text-xs">{fmt(s.createdAt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CustomersPanel({ customers }: { customers: Customer[] }) {
  const router = useRouter();
  const [, startTransition] = useTransition();
  const [q, setQ] = useState('');
  const [workingKey, setWorkingKey] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ key: string; text: string; ok: boolean } | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const filtered = customers.filter((c) => {
    const term = q.toLowerCase();
    const lk = c.credentials?.[0]?.licenseKey?.toLowerCase() || '';
    return (
      c.name.toLowerCase().includes(term) ||
      c.email.toLowerCase().includes(term) ||
      (c.phone || '').includes(term) ||
      lk.includes(term)
    );
  });

  async function handleAddCredits(licenseKey: string) {
    setWorkingKey(licenseKey);
    setMsg(null);
    try {
      const res = await fetch('/api/admin/licenses/add-credits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ licenseKey, credits: 100 }),
      });
      const data = await res.json();
      setMsg({ key: licenseKey, text: data.message || '+100 créditos', ok: res.ok });
      if (res.ok) startTransition(() => router.refresh());
    } catch {
      setMsg({ key: licenseKey, text: 'Erro de conexão', ok: false });
    } finally {
      setWorkingKey(null);
    }
  }

  async function handleUnbind(licenseKey: string) {
    setWorkingKey(licenseKey);
    setMsg(null);
    try {
      const res = await fetch('/api/admin/licenses/unbind', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ licenseKey }),
      });
      const data = await res.json();
      setMsg({ key: licenseKey, text: data.message || 'HWID resetado', ok: res.ok });
      if (res.ok) startTransition(() => router.refresh());
    } catch {
      setMsg({ key: licenseKey, text: 'Erro de conexão', ok: false });
    } finally {
      setWorkingKey(null);
    }
  }

  async function handleToggle(licenseKey: string) {
    setWorkingKey(licenseKey);
    setMsg(null);
    try {
      const res = await fetch('/api/admin/licenses/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ licenseKey }),
      });
      const data = await res.json();
      setMsg({ key: licenseKey, text: data.message || 'Status alterado', ok: res.ok });
      if (res.ok) startTransition(() => router.refresh());
    } catch {
      setMsg({ key: licenseKey, text: 'Erro de conexão', ok: false });
    } finally {
      setWorkingKey(null);
    }
  }

  const copyToClipboard = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Barra de Busca do CRM */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-surface/50 p-4 rounded-xl border border-border">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-secondary" />
          <input
            type="text"
            placeholder="Buscar por nome, e-mail, telefone ou chave..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm bg-background border border-border rounded-lg text-text-primary placeholder:text-text-secondary focus:outline-none focus:border-brand"
          />
        </div>
        <div className="text-xs text-text-secondary w-full sm:w-auto text-right">
          Total de Clientes no CRM: <strong className="text-text-primary">{filtered.length}</strong>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-text-secondary text-xs uppercase tracking-wider">
              <th className="text-left py-3 px-4 font-medium">Cliente</th>
              <th className="text-left py-3 px-4 font-medium">WhatsApp / Contato</th>
              <th className="text-left py-3 px-4 font-medium">Chave de Licença (Railway)</th>
              <th className="text-left py-3 px-4 font-medium">Créditos</th>
              <th className="text-left py-3 px-4 font-medium">Cadastro</th>
              <th className="text-left py-3 px-4 font-medium">Ações de Suporte (CRM)</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="py-12 text-center text-text-secondary">
                  Nenhum cliente encontrado.
                </td>
              </tr>
            )}
            {filtered.map((c) => {
              const cleanPhone = (c.phone || '').replace(/\D/g, '');
              const waNumber = cleanPhone.startsWith('55') ? cleanPhone : `55${cleanPhone}`;
              const waText = encodeURIComponent(
                `Olá ${c.name}, aqui é da equipe do Forja Viral! Como estão seus cortes? Precisa de alguma ajuda?`
              );
              const waUrl = cleanPhone ? `https://wa.me/${waNumber}?text=${waText}` : null;
              const primaryCred = c.credentials?.[0];
              const lk = primaryCred?.licenseKey;

              return (
                <tr key={c.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                  {/* Nome e E-mail */}
                  <td className="py-3 px-4">
                    <div className="font-semibold text-text-primary">{c.name}</div>
                    <div className="text-xs text-text-secondary">{c.email}</div>
                  </td>

                  {/* WhatsApp */}
                  <td className="py-3 px-4">
                    {waUrl ? (
                      <a
                        href={waUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 transition-colors text-xs font-semibold"
                      >
                        <MessageCircle className="h-3.5 w-3.5" />
                        {c.phone}
                      </a>
                    ) : (
                      <span className="text-xs text-text-secondary">{c.phone || 'Sem número'}</span>
                    )}
                  </td>

                  {/* Chave de Licença */}
                  <td className="py-3 px-4">
                    {lk ? (
                      <div className="flex items-center gap-2">
                        <code className="font-mono text-xs text-brand font-bold bg-brand/10 px-2 py-0.5 rounded border border-brand/20">
                          {lk}
                        </code>
                        <button
                          onClick={() => copyToClipboard(lk)}
                          title="Copiar chave"
                          className="text-text-secondary hover:text-text-primary"
                        >
                          <Copy className="h-3.5 w-3.5" />
                        </button>
                        {copiedKey === lk && <span className="text-[10px] text-emerald-400">Copiada!</span>}
                      </div>
                    ) : (
                      <span className="text-xs text-text-secondary italic">Sem chave</span>
                    )}
                  </td>

                  {/* Saldo de Créditos */}
                  <td className="py-3 px-4 font-semibold text-text-primary">
                    <span className="inline-flex items-center gap-1">
                      <Zap className="h-3.5 w-3.5 text-brand" />
                      {primaryCred?.credits ?? 0}
                    </span>
                  </td>

                  {/* Data Cadastro */}
                  <td className="py-3 px-4 text-text-secondary text-xs">{fmt(c.createdAt)}</td>

                  {/* Ações CRM */}
                  <td className="py-3 px-4">
                    {lk ? (
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {/* Adicionar +100 Créditos */}
                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={workingKey === lk}
                            onClick={() => handleAddCredits(lk)}
                            className="text-xs h-7 px-2"
                            title="Recarregar +100 créditos no servidor Railway"
                          >
                            <PlusCircle className="h-3 w-3 mr-1 text-brand" /> +100 Créditos
                          </Button>

                          {/* Resetar HWID (Unbind PC) */}
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={workingKey === lk}
                            onClick={() => handleUnbind(lk)}
                            className="text-xs h-7 px-2 text-text-secondary hover:text-text-primary"
                            title="Desvincular HWID / Trocar de Computador"
                          >
                            <RotateCcw className="h-3 w-3 mr-1" /> Resetar PC
                          </Button>

                          {/* Bloquear / Ativar */}
                          <Button
                            variant="danger"
                            size="sm"
                            disabled={workingKey === lk}
                            onClick={() => handleToggle(lk)}
                            className="text-xs h-7 px-2"
                            title="Bloquear ou reativar licença"
                          >
                            <ShieldOff className="h-3 w-3" />
                          </Button>
                        </div>

                        {msg?.key === lk && (
                          <span className={`text-[11px] ${msg.ok ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {msg.text}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-text-secondary">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CredentialsPanel({ credentials }: { credentials: Credential[] }) {
  const router = useRouter();
  const [, startTransition] = useTransition();
  const [working, setWorking] = useState<{ id: string; action: string } | null>(null);
  const [msgs, setMsgs] = useState<Record<string, { text: string; ok: boolean }>>({});

  async function doAction(credId: string, action: 'revoke' | 'regenerate') {
    setWorking({ id: credId, action });
    try {
      const res = await fetch(`/api/admin/credentials/${credId}/${action}`, { method: 'POST' });
      const data = await res.json();
      setMsgs((m) => ({
        ...m,
        [credId]: { text: data.message ?? (res.ok ? 'OK' : 'Erro'), ok: res.ok },
      }));
      if (res.ok) startTransition(() => router.refresh());
    } catch {
      setMsgs((m) => ({ ...m, [credId]: { text: 'Erro de rede', ok: false } }));
    } finally {
      setWorking(null);
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-text-secondary text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-4 font-medium">Usuário</th>
            <th className="text-left py-3 px-4 font-medium">Chave de Licença</th>
            <th className="text-left py-3 px-4 font-medium">Cliente</th>
            <th className="text-left py-3 px-4 font-medium">URL de Acesso</th>
            <th className="text-left py-3 px-4 font-medium">Railway</th>
            <th className="text-left py-3 px-4 font-medium">Status</th>
            <th className="text-left py-3 px-4 font-medium">Expira</th>
            <th className="text-left py-3 px-4 font-medium">Ações</th>
          </tr>
        </thead>
        <tbody>
          {credentials.length === 0 && (
            <tr>
              <td colSpan={7} className="py-12 text-center text-text-secondary">Nenhuma credencial ainda.</td>
            </tr>
          )}
          {credentials.map((c) => (
            <tr key={c.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td className="py-3 px-4 font-mono text-xs text-text-primary">{c.username}</td>
              <td className="py-3 px-4 font-mono text-xs text-brand font-bold">{c.licenseKey || '—'}</td>
              <td className="py-3 px-4">
                <div className="font-medium text-text-primary">{c.customer.name}</div>
                <div className="text-xs text-text-secondary">{c.customer.email}</div>
              </td>
              <td className="py-3 px-4">
                <a
                  href={c.accessUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-brand hover:underline text-xs"
                >
                  Abrir <ExternalLink className="w-3 h-3" />
                </a>
              </td>
              <td className="py-3 px-4 text-xs text-text-secondary">
                {c.railwayAppUrl ? (
                  <a href={c.railwayAppUrl} target="_blank" rel="noreferrer" className="text-brand hover:underline inline-flex items-center gap-1">
                    Railway <ExternalLink className="w-3 h-3" />
                  </a>
                ) : '—'}
              </td>
              <td className="py-3 px-4"><StatusBadge status={c.status} /></td>
              <td className="py-3 px-4 text-text-secondary text-xs">{fmt(c.expiresAt)}</td>
              <td className="py-3 px-4">
                <div className="flex flex-col gap-1">
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={!!working}
                      onClick={() => doAction(c.id, 'regenerate')}
                      title="Regenerar token"
                    >
                      <RotateCcw className="w-3 h-3" />
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      disabled={!!working || c.status === 'revoked'}
                      onClick={() => doAction(c.id, 'revoke')}
                      title="Revogar acesso"
                    >
                      <ShieldOff className="w-3 h-3" />
                    </Button>
                  </div>
                  {msgs[c.id]?.text && (
                    <span className={cn('text-xs', msgs[c.id].ok ? 'text-success' : 'text-error')}>
                      {msgs[c.id].text}
                    </span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EventsPanel({ events }: { events: WebhookEvent[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-text-secondary text-xs uppercase tracking-wider">
            <th className="text-left py-3 px-4 font-medium">Event ID</th>
            <th className="text-left py-3 px-4 font-medium">Provedor</th>
            <th className="text-left py-3 px-4 font-medium">Tipo</th>
            <th className="text-left py-3 px-4 font-medium">Pedido</th>
            <th className="text-left py-3 px-4 font-medium">Processado</th>
            <th className="text-left py-3 px-4 font-medium">Recebido</th>
          </tr>
        </thead>
        <tbody>
          {events.length === 0 && (
            <tr>
              <td colSpan={6} className="py-12 text-center text-text-secondary">Nenhum evento ainda.</td>
            </tr>
          )}
          {events.map((e) => (
            <>
              <tr
                key={e.id}
                className="border-b border-white/5 hover:bg-white/[0.02] transition-colors cursor-pointer"
                onClick={() => setExpanded(expanded === e.id ? null : e.id)}
              >
                <td className="py-3 px-4 font-mono text-xs text-text-secondary">{e.eventId.slice(-12)}</td>
                <td className="py-3 px-4 text-text-secondary">{e.provider}</td>
                <td className="py-3 px-4">
                  <span className="font-mono text-xs bg-surface rounded px-1.5 py-0.5 text-brand">{e.type}</span>
                </td>
                <td className="py-3 px-4 font-mono text-xs text-text-secondary">{e.orderId?.slice(-8) ?? '—'}</td>
                <td className="py-3 px-4">
                  {e.processed
                    ? <CheckCircle2 className="w-4 h-4 text-success" />
                    : <Clock className="w-4 h-4 text-brand" />
                  }
                </td>
                <td className="py-3 px-4 text-text-secondary text-xs">{fmt(e.createdAt)}</td>
              </tr>
              {expanded === e.id && (
                <tr key={`${e.id}-detail`} className="bg-surface/50">
                  <td colSpan={6} className="px-4 py-3">
                    <pre className="text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap break-all bg-background rounded-lg p-3 border border-white/10 max-h-48">
                      {JSON.stringify(e, null, 2)}
                    </pre>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon: Icon,
  accent = false,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        'rounded-2xl border p-5 flex items-start gap-4 transition-colors',
        accent ? 'border-brand/30 bg-brand/10' : 'border-white/10 bg-surface'
      )}
    >
      <div className={cn('rounded-xl p-2.5', accent ? 'bg-brand/20' : 'bg-surface-elevated')}>
        <Icon className={cn('w-5 h-5', accent ? 'text-brand' : 'text-text-secondary')} />
      </div>
      <div>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
        <p className="text-xs text-text-secondary mt-0.5">{label}</p>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function AdminShell({
  orders,
  subscriptions,
  customers,
  credentials,
  events,
}: AdminShellProps) {
  const [activeTab, setActiveTab] = useState<TabId>('orders');
  const router = useRouter();

  const paidOrders = orders.filter((o) => o.status === 'paid').length;
  const activeSubs = subscriptions.filter((s) => s.status === 'active').length;
  const revenue = orders
    .filter((o) => o.status === 'paid')
    .reduce((acc, o) => acc + o.amount, 0);

  async function logout() {
    await fetch('/api/admin/logout', { method: 'POST' });
    router.push('/admin/login');
  }

  const panels: Record<TabId, React.ReactNode> = {
    orders: <OrdersPanel orders={orders} />,
    subscriptions: <SubscriptionsPanel subscriptions={subscriptions} />,
    customers: <CustomersPanel customers={customers} />,
    credentials: <CredentialsPanel credentials={credentials} />,
    events: <EventsPanel events={events} />,
  };

  const counts: Record<TabId, number> = {
    orders: orders.length,
    subscriptions: subscriptions.length,
    customers: customers.length,
    credentials: credentials.length,
    events: events.length,
  };

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Header */}
      <header className="border-b border-white/10 bg-surface/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-screen-xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-gradient flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-text-primary">Forja Viral</span>
            <ChevronRight className="w-4 h-4 text-text-secondary" />
            <span className="text-text-secondary text-sm">Admin</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-text-secondary hover:text-error"
          >
            <LogOut className="w-4 h-4" />
            Sair
          </Button>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6 py-8 space-y-8">
        {/* Stats row */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Receita (pagos)" value={formatPrice(revenue)} icon={ShoppingCart} accent />
          <StatCard label="Pedidos pagos" value={paidOrders} icon={CheckCircle2} />
          <StatCard label="Assinaturas ativas" value={activeSubs} icon={RefreshCcw} />
          <StatCard label="Clientes" value={customers.length} icon={Users} />
        </section>

        {/* Tab panel */}
        <section className="rounded-2xl border border-white/10 bg-surface overflow-hidden">
          {/* Tab bar */}
          <div className="flex gap-0 border-b border-white/10 overflow-x-auto">
            {TABS.map(({ id, label, Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={cn(
                  'flex items-center gap-2 px-5 py-4 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px',
                  activeTab === id
                    ? 'border-brand text-brand bg-brand/5'
                    : 'border-transparent text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
                <span
                  className={cn(
                    'ml-1 rounded-full px-1.5 py-0.5 text-xs font-mono',
                    activeTab === id
                      ? 'bg-brand/20 text-brand'
                      : 'bg-surface-elevated text-text-secondary'
                  )}
                >
                  {counts[id]}
                </span>
              </button>
            ))}
          </div>

          {/* Panel content */}
          <div className="min-h-[400px]">{panels[activeTab]}</div>
        </section>
      </main>
    </div>
  );
}
