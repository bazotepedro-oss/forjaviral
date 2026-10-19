// Railway / app hosting integration helpers.
// The app is already hosted; this layer only resolves URLs and (optionally) calls an internal provision endpoint.

export function getRailwayAppUrl(): string {
  return (process.env.RAILWAY_APP_URL || '').replace(/\/$/, '');
}

export function getRailwayProjectUrl(): string {
  return (process.env.RAILWAY_PROJECT_URL || '').replace(/\/$/, '');
}

export function isRailwayConfigured(): boolean {
  return Boolean(process.env.RAILWAY_APP_URL);
}

export function buildAppAccessUrl(token?: string): string {
  const base = getRailwayAppUrl();
  if (!base) return '';
  if (!token) return base;
  return `${base}/acesso?token=${encodeURIComponent(token)}`;
}