// AbacatePay integration layer oficial (v2 nativo com fallback v1).
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
  return process.env.ABACATEPAY_WEBHOOK_SECRET || 'test-secret';
}

function baseUrl(): string {
  return (process.env.ABACATEPAY_BASE_URL || 'https://api.abacatepay.com').replace(/\/$/, '');
}

/**
 * Obtém ou cria o produto na AbacatePay v2.
 */
async function getOrCreateV2Product(
  key: string,
  base: string,
  externalId: string,
  name: string,
  priceInCents: number
): Promise<string> {
  // 1. Tenta listar produtos e achar pelo externalId
  try {
    const listRes = await fetch(`${base}/v2/products/list`, {
      headers: { Authorization: `Bearer ${key}` },
    });
    if (listRes.ok) {
      const listJson = await listRes.json();
      const existing = (listJson.data || []).find((p: any) => p.externalId === externalId);
      if (existing?.id) return existing.id;
    }
  } catch (err) {
    console.warn('[AbacatePay v2] Falha ao listar produtos:', err);
  }

  // 2. Se não encontrou, cria o produto
  const createRes = await fetch(`${base}/v2/products/create`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      externalId,
      name,
      price: priceInCents,
      currency: 'BRL',
      description: `Forja Viral - ${name}`,
    }),
  });

  const createJson = await createRes.json();
  if (createJson.success && createJson.data?.id) {
    return createJson.data.id;
  }

  // Se já existia e não pegou na listagem por paginação, tenta listar novamente
  if (createJson.error && String(createJson.error).includes('already exists')) {
    const retryList = await fetch(`${base}/v2/products/list?limit=100`, {
      headers: { Authorization: `Bearer ${key}` },
    });
    const retryJson = await retryList.json();
    const found = (retryJson.data || []).find((p: any) => p.externalId === externalId);
    if (found?.id) return found.id;
  }

  throw new Error(`Falha ao registrar produto na AbacatePay: ${createJson.error || 'Erro desconhecido'}`);
}

/**
 * Cria ou recupera o cliente na AbacatePay v2 para vincular ao checkout.
 */
async function getOrCreateV2Customer(
  key: string,
  base: string,
  customer: AbacatePayCustomer
): Promise<string | undefined> {
  try {
    const cleanPhone = (customer.phone || '').replace(/\D/g, '');
    const res = await fetch(`${base}/v2/customers/create`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: customer.name,
        email: customer.email,
        cellphone: cleanPhone || undefined,
      }),
    });
    const json = await res.json();
    if (json.success && json.data?.id) {
      return json.data.id;
    }
  } catch (e) {
    console.warn('[AbacatePay v2] Aviso ao criar cliente:', e);
  }
  return undefined;
}

/**
 * Cria uma sessão de checkout / billing na AbacatePay (v2 com fallback v1).
 */
export async function createCheckout(
  input: AbacatePayCheckoutInput
): Promise<AbacatePayCheckoutResponse> {
  const key = apiKey();
  const base = baseUrl();

  const completionUrl = input.returnURL.includes('/retorno')
    ? `${input.returnURL.replace('/retorno', '')}/acesso?orderId=${encodeURIComponent(input.metadata.orderId || '')}`
    : input.returnURL;

  // ── 1. Tenta API v2 Nativa ──
  try {
    const prodExternalId = `${input.planSlug}_${input.amount}`;
    const prodName = input.appName || 'Pacote de Créditos Forja Viral';
    const productId = await getOrCreateV2Product(key, base, prodExternalId, prodName, input.amount);

    const customerId = await getOrCreateV2Customer(key, base, input.customer);

    const v2Payload: any = {
      items: [{ id: productId, quantity: 1 }],
      methods: ['PIX'],
      returnUrl: input.returnURL,
      completionUrl,
      metadata: input.metadata,
    };
    if (customerId) v2Payload.customerId = customerId;

    const resV2 = await fetch(`${base}/v2/checkouts/create`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(v2Payload),
    });

    const jsonV2 = await resV2.json();
    if (jsonV2.success && jsonV2.data?.url) {
      return {
        checkoutURL: jsonV2.data.url,
        checkoutId: jsonV2.data.id,
        orderId: input.metadata.orderId,
      };
    }
    console.warn('[AbacatePay v2] Falha no checkouts/create v2, tentando fallback:', jsonV2.error);
  } catch (errV2: any) {
    console.warn('[AbacatePay v2] Erro na chamada v2:', errV2?.message);
  }

  // ── 2. Fallback v1 caso necessário ──
  const v1Body = {
    frequency: 'ONE_TIME',
    methods: ['PIX'],
    products: [
      {
        externalId: input.planSlug,
        name: input.appName || 'Forja Viral',
        quantity: 1,
        price: input.amount,
      },
    ],
    returnUrl: input.returnURL,
    completionUrl,
    customer: {
      name: input.customer.name,
      cellphone: (input.customer.phone || '').replace(/\D/g, ''),
      email: input.customer.email,
    },
    metadata: input.metadata,
  };

  const resV1 = await fetch(`${base}/v1/billing/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify(v1Body),
  });

  const jsonV1 = await resV1.json().catch(() => ({}));
  const d = jsonV1.data || jsonV1;
  const checkoutURL = d.url || d.checkoutURL || d.paymentUrl;
  const checkoutId = d.id || d.checkoutId;

  if (checkoutURL) {
    return {
      checkoutURL,
      checkoutId: String(checkoutId || ''),
      orderId: input.metadata.orderId,
    };
  }

  throw new Error(`Falha ao gerar cobrança AbacatePay: ${jsonV1.error || resV1.statusText}`);
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

  // Em ambiente dev permite sem travar se o secret for o padrão
  if (secret === 'test-secret') return true;

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