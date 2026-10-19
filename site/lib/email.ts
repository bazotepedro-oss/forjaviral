// E-mail service (Resend). Opcional — desativado se RESEND_API_KEY não estiver configurado.
import { Resend } from 'resend';

let resend: Resend | null = null;

function client(): Resend | null {
  const key = process.env.RESEND_API_KEY;
  if (!key) return null;
  if (!resend) resend = new Resend(key);
  return resend;
}

export function isEmailEnabled(): boolean {
  return Boolean(process.env.RESEND_API_KEY);
}

export async function sendAccessEmail(input: {
  to: string;
  name: string;
  accessUrl: string;
  username: string;
  temporaryPassword: string | null;
}): Promise<{ ok: boolean; error?: string }> {
  const c = client();
  if (!c) return { ok: false, error: 'RESEND_API_KEY not configured' };
  const from = process.env.EMAIL_FROM || 'noreply@forjaviral.com';
  const html = `
<!DOCTYPE html><html><body style="font-family:Inter,system-ui,sans-serif;background:#0B0B0B;color:#F5F5F5;padding:24px">
  <div style="max-width:560px;margin:0 auto">
    <h2 style="color:#FF6B1A">Seu acesso à Forja Viral está pronto 🚀</h2>
    <p>Olá, ${input.name}! Seu pagamento foi aprovado e seu acesso foi gerado automaticamente.</p>
    <div style="background:#171717;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;margin:16px 0">
      <p style="margin:0 0 8px"><strong>Link de acesso:</strong><br>
        <a href="${input.accessUrl}" style="color:#FFB27A">${input.accessUrl}</a>
      </p>
      <p style="margin:0 0 8px"><strong>Usuário:</strong> ${input.username}</p>
      ${input.temporaryPassword ? `<p style="margin:0 0 8px"><strong>Senha temporária:</strong> <code style="color:#FFB27A">${input.temporaryPassword}</code></p>` : ''}
      <p style="margin:0;color:#A3A3A3;font-size:12px">Esta senha é temporária — troque ao acessar.</p>
    </div>
    <p style="color:#A3A3A3;font-size:12px">Se você não fez essa compra, ignore este e-mail.</p>
  </div>
</body></html>`;
  const { data, error } = await c.emails.send({
    from,
    to: input.to,
    subject: 'Seu acesso à Forja Viral está pronto',
    html,
  });
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}