// E-mail service (Resend). Envia chave de licença, créditos e link de aulas pós-compra.
import { Resend } from 'resend';

import fs from 'fs';
import path from 'path';

let resend: Resend | null = null;

function client(): Resend | null {
  const key = process.env.RESEND_API_KEY;
  if (!key) return null;
  if (!resend) resend = new Resend(key);
  return resend;
}

function getLogoAttachments() {
  try {
    const logoPath = path.join(process.cwd(), 'public', 'logo.png');
    if (fs.existsSync(logoPath)) {
      const buffer = fs.readFileSync(logoPath);
      return [
        {
          filename: 'logo.png',
          content: buffer,
          contentType: 'image/png',
          inlineContentId: 'brand-logo',
        },
      ];
    }
  } catch (err) {
    console.warn('[E-mail] Aviso ao carregar logo para anexo:', err);
  }
  return [];
}

export function isEmailEnabled(): boolean {
  return Boolean(process.env.RESEND_API_KEY);
}

export interface SendAccessEmailInput {
  to: string;
  name: string;
  licenseKey: string;
  credits: number;
  accessUrl: string;
  courseUrl?: string;
  colabUrl?: string;
  username?: string;
  temporaryPassword?: string | null;
  planName?: string;
}

export interface SendRechargeEmailInput {
  to: string;
  name: string;
  licenseKey: string;
  creditsAdded: number;
  newBalance?: number;
  accessUrl?: string;
}

export async function sendAccessEmail(input: SendAccessEmailInput): Promise<{ ok: boolean; error?: string }> {
  const c = client();
  if (!c) {
    console.warn(`[E-mail] RESEND_API_KEY não configurada no .env. E-mail de boas-vindas para ${input.to} ignorado.`);
    return { ok: false, error: 'RESEND_API_KEY not configured' };
  }

  const from = process.env.EMAIL_FROM || 'Fábrica de Cortes <contato@fabricadecortes.com>';
  const courseLink = input.courseUrl || 'https://youtube.com/playlist?list=PL_fabricadecortes_tutorial';
  const colabLink = input.colabUrl || 'https://colab.research.google.com/github/bazotepedro-oss/forjaviral/blob/main/ViralCutter.ipynb';
  const accessPage = input.accessUrl || `${process.env.NEXT_PUBLIC_APP_URL || 'https://fabricadecortes.com'}/acesso`;
  const planTitle = input.planName || 'Pacote de Créditos Fábrica de Cortes';
  const logoAttachments = getLogoAttachments();

  const html = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Seu acesso à Fábrica de Cortes está pronto</title>
</head>
<body style="margin:0;padding:24px;background-color:#0A0A0A;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#F3F4F6;">
  <div style="max-width:580px;margin:0 auto;background:#141414;border:1px solid #262626;border-radius:18px;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,0.5);">
    
    <!-- Topo / Header -->
    <div style="background:linear-gradient(135deg, #FF5C00, #E04800);padding:32px 24px;text-align:center;">
      <img src="cid:brand-logo" alt="Fábrica de Cortes" style="width:52px;height:52px;border-radius:14px;margin-bottom:12px;box-shadow:0 4px 16px rgba(0,0,0,0.3);display:inline-block;" />
      <h1 style="margin:0;font-size:24px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px;">
        Fábrica de Cortes
      </h1>
      <p style="margin:8px 0 0;font-size:14px;color:rgba(255,255,255,0.9);font-weight:500;">
        Pagamento Confirmado! Seu acesso foi liberado com sucesso.
      </p>
    </div>

    <!-- Conteúdo Principal -->
    <div style="padding:28px 24px;">
      <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#E5E7EB;">
        Olá, <strong>${input.name}</strong>! Obrigado por adquirir a <strong>Fábrica de Cortes</strong> (<a href="https://fabricadecortes.com" style="color:#FF7A1A;text-decoration:none;">fabricadecortes.com</a>). Seus créditos já foram ativados no servidor e estão prontos para uso.
      </p>

      <!-- Card da Chave de Licença -->
      <div style="background:#1C1C1C;border:2px solid #FF5C00;border-radius:14px;padding:20px;margin:20px 0;text-align:center;">
        <span style="display:inline-block;font-size:11px;font-weight:700;color:#FF7A1A;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
          Sua Chave de Ativação Oficial
        </span>
        <div style="background:#0D0D0D;border:1px solid #333333;border-radius:8px;padding:12px;font-family:'Courier New',Courier,monospace;font-size:20px;font-weight:bold;color:#FFFFFF;letter-spacing:2px;user-select:all;margin:6px 0 12px;">
          ${input.licenseKey}
        </div>
        <div style="display:flex;justify-content:center;gap:12px;font-size:13px;color:#A3A3A3;">
          <span>⚡ <strong>${input.credits} Créditos</strong> inclusos</span>
          <span>•</span>
          <span>📅 Validade de <strong>365 dias</strong></span>
        </div>
      </div>

      <!-- Como usar -->
      <div style="background:#1A1A1A;border:1px solid #2B2B2B;border-radius:12px;padding:16px;margin:20px 0;font-size:13px;line-height:1.6;">
        <h3 style="margin:0 0 8px;font-size:14px;color:#FFFFFF;">Como começar a cortar vídeos agora:</h3>
        <ol style="margin:0;padding-left:18px;color:#D1D5DB;">
          <li style="margin-bottom:6px;">Abra a ferramenta no seu <strong>PC local</strong> ou diretamente no <strong>Google Colab</strong> (gratuito na nuvem).</li>
          <li style="margin-bottom:6px;">Vá na aba <strong>Licença / Ativação</strong> e cole sua chave acima.</li>
          <li>Clique em <strong>Verificar / Ativar</strong> e comece a gerar cortes virais com IA!</li>
        </ol>
      </div>

      <!-- Botões de Ação -->
      <div style="text-align:center;margin:28px 0;">
        <a href="${colabLink}" target="_blank" style="display:inline-block;background:#FF5C00;color:#FFFFFF;font-size:14px;font-weight:700;text-decoration:none;padding:13px 24px;border-radius:10px;margin:6px;box-shadow:0 4px 14px rgba(255,92,0,0.35);">
          🚀 Executar no Google Colab
        </a>
        <a href="${courseLink}" target="_blank" style="display:inline-block;background:#262626;border:1px solid #3D3D3D;color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;padding:13px 24px;border-radius:10px;margin:6px;">
          🎓 Assistir Aulas e Tutoriais
        </a>
      </div>

      <!-- Dados de Acesso Web -->
      <div style="border-top:1px solid #262626;padding-top:18px;margin-top:24px;font-size:12px;color:#888888;line-height:1.6;">
        <p style="margin:0 0 6px;">
          <strong>Painel de Acesso Web:</strong> Caso precise consultar seus créditos ou ver sua chave novamente, acesse a qualquer momento:
          <br><a href="${accessPage}" style="color:#FF7A1A;text-decoration:none;">${accessPage}</a>
        </p>
        ${input.username ? `<p style="margin:0 0 4px;"><strong>Usuário:</strong> ${input.username}</p>` : ''}
        ${input.temporaryPassword ? `<p style="margin:0 0 4px;"><strong>Senha provisória:</strong> <code style="color:#FFB27A;">${input.temporaryPassword}</code></p>` : ''}
      </div>

    </div>

    <!-- Rodapé -->
    <div style="background:#0F0F0F;border-top:1px solid #222222;padding:16px 24px;text-align:center;font-size:11px;color:#666666;">
      Fábrica de Cortes — fabricadecortes.com • Tecnologia de Cortes Automáticos com IA.
    </div>

  </div>
</body>
</html>
  `;

  try {
    let result = await c.emails.send({
      from,
      to: input.to,
      subject: `Seu acesso à Fábrica de Cortes está pronto (${input.credits} Créditos) 🚀`,
      html,
      attachments: logoAttachments.length > 0 ? logoAttachments : undefined,
    });
    if (result.error && from !== 'Fábrica de Cortes <onboarding@resend.dev>') {
      console.warn(`[E-mail] Fallback para onboarding@resend.dev após aviso: ${result.error.message}`);
      result = await c.emails.send({
        from: 'Fábrica de Cortes <onboarding@resend.dev>',
        to: input.to,
        subject: `Seu acesso à Fábrica de Cortes está pronto (${input.credits} Créditos) 🚀`,
        html,
        attachments: logoAttachments.length > 0 ? logoAttachments : undefined,
      });
    }
    if (result.error) {
      console.error(`[E-mail] Erro ao enviar e-mail para ${input.to}:`, result.error.message);
      return { ok: false, error: result.error.message };
    }
    console.log(`[E-mail] E-mail de acesso enviado com sucesso para ${input.to}! (ID: ${result.data?.id})`);
    return { ok: true };
  } catch (err: any) {
    console.error(`[E-mail] Falha inesperada ao enviar para ${input.to}:`, err?.message);
    return { ok: false, error: err?.message };
  }
}

export async function sendRechargeEmail(input: SendRechargeEmailInput): Promise<{ ok: boolean; error?: string }> {
  const c = client();
  if (!c) {
    console.warn(`[E-mail] RESEND_API_KEY não configurada. E-mail de recarga para ${input.to} ignorado.`);
    return { ok: false, error: 'RESEND_API_KEY not configured' };
  }

  const from = process.env.EMAIL_FROM || 'Fábrica de Cortes <contato@fabricadecortes.com>';
  const accessPage = input.accessUrl || `${process.env.NEXT_PUBLIC_APP_URL || 'https://fabricadecortes.com'}/acesso`;
  const logoAttachments = getLogoAttachments();

  const html = `
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Recarga Confirmada — Fábrica de Cortes</title>
</head>
<body style="margin:0;padding:24px;background-color:#0A0A0A;font-family:Inter,sans-serif;color:#F3F4F6;">
  <div style="max-width:560px;margin:0 auto;background:#141414;border:1px solid #262626;border-radius:16px;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,0.5);">
    
    <div style="background:linear-gradient(135deg, #FF5C00, #E04800);padding:26px 24px;text-align:center;">
      <img src="cid:brand-logo" alt="Fábrica de Cortes" style="width:48px;height:48px;border-radius:12px;margin-bottom:8px;box-shadow:0 4px 16px rgba(0,0,0,0.3);display:inline-block;" />
      <h2 style="color:#FFFFFF;margin:0;font-size:22px;font-weight:800;">⚡ Recarga Confirmada!</h2>
    </div>

    <div style="padding:26px 24px;">
      <p style="font-size:14px;color:#E5E7EB;margin:0 0 16px;">
        Olá, <strong>${input.name}</strong>! O pagamento da sua recarga foi confirmado e os novos créditos já foram injetados na sua chave de licença.
      </p>

      <div style="background:#1C1C1C;border:1px solid #333333;border-radius:12px;padding:16px;margin:16px 0;">
        <p style="margin:0 0 8px;font-size:13px;color:#A3A3A3;">Chave de Licença recarregada:</p>
        <code style="display:block;background:#0D0D0D;padding:10px;border-radius:6px;font-size:16px;font-weight:bold;color:#FF7A1A;">
          ${input.licenseKey}
        </code>
        <p style="margin:12px 0 0;font-size:14px;color:#FFFFFF;">
          <strong>+${input.creditsAdded} novos créditos</strong> adicionados à sua conta!
        </p>
      </div>

      <p style="font-size:13px;color:#9CA3AF;line-height:1.6;">
        Você já pode abrir a Fábrica de Cortes (<a href="https://fabricadecortes.com" style="color:#FF7A1A;text-decoration:none;">fabricadecortes.com</a>) ou clicar em <strong>"Atualizar créditos"</strong> na ferramenta para utilizar seus novos vídeos imediatamente.
      </p>

      <div style="margin-top:24px;text-align:center;">
        <a href="${accessPage}" style="display:inline-block;background:#FF5C00;color:#FFFFFF;text-decoration:none;font-weight:700;font-size:13px;padding:12px 24px;border-radius:8px;">
          Ver Meus Créditos no Painel
        </a>
      </div>
    </div>
  </div>
</body>
</html>
  `;

  try {
    let result = await c.emails.send({
      from,
      to: input.to,
      subject: `+${input.creditsAdded} Créditos adicionados à sua Fábrica de Cortes ⚡`,
      html,
      attachments: logoAttachments.length > 0 ? logoAttachments : undefined,
    });
    if (result.error && from !== 'Fábrica de Cortes <onboarding@resend.dev>') {
      result = await c.emails.send({
        from: 'Fábrica de Cortes <onboarding@resend.dev>',
        to: input.to,
        subject: `+${input.creditsAdded} Créditos adicionados à sua Fábrica de Cortes ⚡`,
        html,
        attachments: logoAttachments.length > 0 ? logoAttachments : undefined,
      });
    }
    if (result.error) return { ok: false, error: result.error.message };
    return { ok: true };
  } catch (err: any) {
    return { ok: false, error: err?.message };
  }
}