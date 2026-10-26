// Integração do Site com o Forja Viral License Server (Railway + Postgres)

export interface CreateLicenseParams {
  licenseKey: string;
  credits: number;
  days: number;
  plan: string;
}

export function getLicenseServerUrl(): string {
  return (
    process.env.FORJA_LICENSE_SERVER_URL ||
    'https://forja-license-production.up.railway.app'
  ).replace(/\/$/, '');
}

export function getLicenseAdminToken(): string {
  return process.env.FORJA_LICENSE_ADMIN_TOKEN || 'FV291125';
}

export interface RailwayLicense {
  license_key: string;
  hwid?: string | null;
  exp: number;
  credits: number;
  plan: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Busca todas as licenças diretamente do PostgreSQL do Railway via JSON API.
 */
export async function listLicensesFromServer(): Promise<RailwayLicense[]> {
  const url = `${getLicenseServerUrl()}/admin/api/licenses?token=${encodeURIComponent(getLicenseAdminToken())}`;
  try {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return [];
    const json = await res.json();
    return json.licenses || [];
  } catch (e) {
    console.error('Falha ao listar licenças do Railway:', e);
    return [];
  }
}

/**
 * Cria uma nova licença no servidor Railway com créditos e dias de validade.
 */
export async function createLicenseOnServer(params: CreateLicenseParams): Promise<{ ok: boolean; message?: string }> {
  const url = `${getLicenseServerUrl()}/admin/action?token=${encodeURIComponent(getLicenseAdminToken())}`;
  const body = new URLSearchParams({
    action: 'create',
    license_key: params.licenseKey,
    credits: String(params.credits || 100),
    days: String(params.days || 30),
    plan: params.plan || 'custom',
  });

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      redirect: 'manual',
    });

    if (res.status === 200 || res.status === 303 || res.status === 302) {
      return { ok: true, message: 'Licença criada com sucesso no servidor Railway' };
    }
    const txt = await res.text().catch(() => '');
    return { ok: false, message: `Falha ao criar licença (${res.status}): ${txt}` };
  } catch (err: any) {
    console.error('Erro ao conectar ao License Server:', err);
    return { ok: false, message: err?.message || 'Erro de conexão com o License Server' };
  }
}

/**
 * Recarrega/adiciona créditos à licença existente do cliente.
 */
export async function addCreditsOnServer(licenseKey: string, creditsToAdd: number): Promise<{ ok: boolean; message?: string }> {
  const url = `${getLicenseServerUrl()}/admin/action?token=${encodeURIComponent(getLicenseAdminToken())}`;
  const body = new URLSearchParams({
    action: 'add_credits',
    license_key: licenseKey,
    add: String(creditsToAdd),
  });

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      redirect: 'manual',
    });

    if (res.status === 200 || res.status === 303 || res.status === 302) {
      return { ok: true, message: `+${creditsToAdd} créditos adicionados com sucesso` };
    }
    const txt = await res.text().catch(() => '');
    return { ok: false, message: `Erro ao adicionar créditos (${res.status}): ${txt}` };
  } catch (err: any) {
    return { ok: false, message: err?.message || 'Erro de conexão' };
  }
}

/**
 * Reseta o HWID (Unbind) para o cliente poder trocar de PC.
 */
export async function unbindHwidOnServer(licenseKey: string): Promise<{ ok: boolean; message?: string }> {
  const url = `${getLicenseServerUrl()}/admin/action?token=${encodeURIComponent(getLicenseAdminToken())}`;
  const body = new URLSearchParams({
    action: 'unbind',
    license_key: licenseKey,
  });

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      redirect: 'manual',
    });

    return { ok: true, message: 'HWID resetado com sucesso' };
  } catch (err: any) {
    return { ok: false, message: err?.message || 'Erro ao resetar HWID' };
  }
}

/**
 * Bloqueia ou ativa uma licença no servidor Railway.
 */
export async function toggleLicenseOnServer(licenseKey: string): Promise<{ ok: boolean; message?: string }> {
  const url = `${getLicenseServerUrl()}/admin/action?token=${encodeURIComponent(getLicenseAdminToken())}`;
  const body = new URLSearchParams({
    action: 'toggle',
    license_key: licenseKey,
  });

  try {
    await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      redirect: 'manual',
    });

    return { ok: true, message: 'Status alternado com sucesso' };
  } catch (err: any) {
    return { ok: false, message: err?.message || 'Erro ao alterar status' };
  }
}

/**
 * Estende a validade da licença em N dias no servidor Railway.
 */
export async function extendDaysOnServer(licenseKey: string, days: number): Promise<{ ok: boolean; message?: string }> {
  const url = `${getLicenseServerUrl()}/admin/action?token=${encodeURIComponent(getLicenseAdminToken())}`;
  const body = new URLSearchParams({
    action: 'extend_days',
    license_key: licenseKey,
    days: String(days),
  });

  try {
    await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      redirect: 'manual',
    });

    return { ok: true, message: `+${days} dias adicionados com sucesso` };
  } catch (err: any) {
    return { ok: false, message: err?.message || 'Erro ao estender validade' };
  }
}

/**
 * Deleta permanentemente uma licença no servidor Railway.
 */
export async function deleteLicenseOnServer(licenseKey: string): Promise<{ ok: boolean; message?: string }> {
  const url = `${getLicenseServerUrl()}/admin/action?token=${encodeURIComponent(getLicenseAdminToken())}`;
  const body = new URLSearchParams({
    action: 'delete',
    license_key: licenseKey,
  });

  try {
    await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
      redirect: 'manual',
    });

    return { ok: true, message: 'Licença removida com sucesso do Railway' };
  } catch (err: any) {
    return { ok: false, message: err?.message || 'Erro ao deletar licença' };
  }
}

/**
 * Gera uma chave de licença no padrão Fábrica de Cortes: FC-XXXXX-XXXXX
 */
export function generateLicenseKey(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const part1 = Array.from({ length: 5 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  const part2 = Array.from({ length: 5 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  return `FC-${part1}-${part2}`;
}
