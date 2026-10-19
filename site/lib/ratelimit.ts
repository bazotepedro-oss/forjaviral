// Rate limiting em memória (single-process). Em multi-processo, use Redis.
const store = new Map<string, { count: number; resetAt: number }>();

export interface RateLimitOptions {
  max?: number;
  windowMs?: number;
  keyPrefix?: string;
}

export function rateLimit(
  key: string,
  options: RateLimitOptions = {}
): { ok: boolean; remaining: number; resetAt: number } {
  const max = options.max ?? parseInt(process.env.RATE_LIMIT_MAX || '60', 10);
  const windowMs = options.windowMs ?? parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10);
  const fullKey = `${options.keyPrefix || 'rl'}:${key}`;
  const now = Date.now();
  const entry = store.get(fullKey);
  if (!entry || entry.resetAt < now) {
    const resetAt = now + windowMs;
    store.set(fullKey, { count: 1, resetAt });
    return { ok: true, remaining: max - 1, resetAt };
  }
  entry.count += 1;
  return {
    ok: entry.count <= max,
    remaining: Math.max(0, max - entry.count),
    resetAt: entry.resetAt,
  };
}

// Limpeza periódica
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of store.entries()) {
    if (v.resetAt < now) store.delete(k);
  }
}, 60000);