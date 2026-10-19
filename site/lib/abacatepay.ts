// AbacatePay integration layer oficial (v1/v2).
// Suporte a cobranças Pix, checkout hospedado e webhooks com assinatura HMAC.

import { verifyHmac } from './utils';

export type AbacatePayStatus =
  | 'paid'
  | 'pending'
  | 'failed'
  | 'canceled'
  | 'refunded'
  | 'expired';

export interface AbacatePayCustomer {
  name: string;
  email: string;
  phone?: string;
}

export interface AbacatePayCheckoutInput {
  planSlug: string;
  planId: string;
  amount: number; // cents
  currency: 'BRL';
  customer: AbacatePayCustomer;
  metadata: Record<string, string>;
  returnURL: string;
  appName: string;
}

export interface AbacatePayCheckoutResponse {
  checkoutURL: string;
  checkoutId: string;
  orderId?: string;
}

export interface AbacatePayWebhookEvent {
  id?: string;
  event?: string;
  type?: string;
  data: {
    id?: string;
    status?: string;
    checkoutId?: string;
    orderId?: string;
    subscriptionId?: string;
    amount?: number;
    metadata?: Record<string, string>;
  };
}

function apiKey(): string {
  const key = process.env.ABACATEPAY_API_KEY;
  if (!key) throw new Error('ABACATEPAY_API_KEY não configurada');
  return key;
}

function webhookSecret(): string {
  const s = process.env.ABACATEPAY_WEBHOOK_SECRET;
  if (!s) throw new Error('ABACATEPAY_WEBHOOK_SECRET não configurado');
  return s;
}

function baseUrl(): string {
  return (process.env.ABACATEPAY_BASE_URL || 'https://api.abacatepay.com').replace(/\/$/, '');
}

/**
 * Cria uma sessão de checkout / billing na AbacatePay.
 */
export async function createCheckout(
  input: AbacatePayCheckoutInput
): Promise<AbacatePayCheckoutResponse> {
  const key = apiKey();
  const base = baseUrl();

  // Payload formatado de acordo com a documentação oficial da AbacatePay
  const body = {
    frequency: 'ONE_TIME',
    methods: ['PIX'],
    products: [
      {
        externalId: input.planSlug,
        name: input.appName || 'Forja Viral',
        quantity: 1,
        price: input.amount, // em centavos
      },
    ],
    returnUrl: input.returnURL,
    completionUrl: input.returnURL.includes('/retorno')
      ? `${input.returnURL.replace('/retorno', '')}/acesso?orderId=${encodeURIComponent(input.metadata.orderId || '')}`
      : input.returnURL,
    customer: {
      name: input.customer.name,
      cellphone: (input.customer.phone || '').replace(/\D/g, ''),
      email: input.customer.email,
    },
    metadata: input.metadata,
  };

  // Tenta primeiro o endpoint oficial /v1/billing/create
  let res = await fetch(`${base}/v1/billing/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify(body),
  });

  // Se a rota for diferente dependendo da versão da conta, tenta fallback para /v1/checkouts/create
  if (!res.ok && res.status === 404) {
    res = await fetch(`${base}/v1/checkouts/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify(body),
    });
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`AbacatePay falhou (${res.status}): ${text}`);
  }

  const json = await res.json();
  const d = json.data || json;

  const checkoutURL = d.url || d.checkoutURL || d.paymentUrl || json.checkoutURL;
  const checkoutId = d.id || d.checkoutId || json.id || json.checkoutId;
  const orderId = d.orderId || d.order_id || json.orderId;

  if (!checkoutURL) {
    throw new Error('AbacatePay não retornou URL de pagamento');
  }

  return {
    checkoutURL,
    checkoutId: String(checkoutId || ''),
    orderId: orderId ? String(orderId) : undefined,
  };
}

/**
 * Valida a assinatura ou o secret do webhook enviado pela AbacatePay.
 */
export function verifyWebhookSignature(
  payload: string,
  signature: string | null,
  querySecret?: string | null
): boolean {
  const secret = webhookSecret();

  // 1. Verificação por query secret (ex: ?webhookSecret=xyz)
  if (querySecret && querySecret === secret) {
    return true;
  }

  // 2. Verificação por HMAC SHA-256 no header
  if (signature) {
    try {
      return verifyHmac(payload, signature, secret);
    } catch {
      return false;
    }
  }

  return false;
}

/**
 * Faz o parse seguro do evento de webhook recebido.
 */
export function parseWebhookEvent(payload: string): AbacatePayWebhookEvent {
  const parsed = JSON.parse(payload);
  return {
    id: parsed.id || parsed.eventId,
    type: parsed.event || parsed.type || 'unknown',
    data: parsed.data || parsed,
  };
}

/**
 * Mapeia os status retornados pela AbacatePay para os status do sistema.
 */
export function mapStatus(status?: string): string {
  const s = (status || '').toLowerCase();
  switch (s) {
    case 'paid':
    case 'completed':
    case 'confirmed':
      return 'paid';
    case 'pending':
    case 'processing':
      return 'pending';
    case 'failed':
      return 'failed';
    case 'canceled':
    case 'cancelled':
      return 'canceled';
    case 'refunded':
      return 'refunded';
    case 'expired':
      return 'failed';
    default:
      return 'pending';
  }
}

export function getPlanId(slug: string): string | undefined {
  const raw = process.env.ABACATEPAY_PLAN_IDS;
  if (!raw) return undefined;
  try {
    const map = JSON.parse(raw) as Record<string, string>;
    return map[slug];
  } catch {
    return undefined;
  }
}