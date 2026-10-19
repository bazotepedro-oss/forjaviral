// Provisioning layer: gera credenciais de acesso, chave de licença no Railway e entrega de curso.

import { randomBytes } from 'crypto';
import bcrypt from 'bcryptjs';
import { prisma } from './db';
import { generateToken, hashToken, signHmac } from './utils';
import { generateLicenseKey, createLicenseOnServer } from './license-server';

export interface ProvisionInput {
  customerId: string;
  orderId: string;
  subscriptionId?: string;
  email: string;
  plan: string;
}

export interface ProvisionResult {
  credentialId: string;
  username: string;
  temporaryPassword: string | null;
  accessToken: string;
  accessUrl: string;
  licenseKey: string;
  credits: number;
  courseUrl: string;
  colabUrl: string;
  expiresAt: Date;
}

const SALT_ROUNDS = 10;

function generateUsername(email: string): string {
  const base = email.split('@')[0].toLowerCase().replace(/[^a-z0-9._-]/g, '');
  const suffix = randomBytes(2).toString('hex');
  return `${base}_${suffix}`;
}

function generatePassword(length = 12): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#';
  let out = '';
  const bytes = randomBytes(length);
  for (let i = 0; i < length; i++) {
    out += chars[bytes[i] % chars.length];
  }
  return out;
}

export function courseUrl(): string {
  return process.env.COURSE_URL || 'https://youtube.com/playlist?list=PL_forjaviral_tutorial';
}

export function colabUrl(): string {
  return (
    process.env.COLAB_NOTEBOOK_URL ||
    'https://colab.research.google.com/github/bazotepedro-oss/forjaviral/blob/main/ViralCutter.ipynb'
  );
}

export function appBaseUrl(): string {
  return process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
}

function getPlanSpecs(planSlug: string): { credits: number; days: number } {
  const s = (planSlug || '').toLowerCase();
  if (s.includes('pro') || s.includes('250')) {
    return { credits: 250, days: 365 };
  }
  if (s.includes('escala') || s.includes('120') || s.includes('trimestral') || s.includes('anual')) {
    return { credits: 120, days: 365 };
  }
  if (s.includes('criador') || s.includes('50') || s.includes('mensal')) {
    return { credits: 50, days: 365 };
  }
  if (s.includes('iniciante') || s.includes('30')) {
    return { credits: 30, days: 365 };
  }
  if (s.includes('teste') || s.includes('15')) {
    return { credits: 15, days: 365 };
  }
  return { credits: 50, days: 365 };
}

export async function provision(input: ProvisionInput): Promise<ProvisionResult> {
  const username = generateUsername(input.email);
  const temporaryPassword = generatePassword();
  const passwordHash = await bcrypt.hash(temporaryPassword, SALT_ROUNDS);

  // Token de acesso rápido à página de acesso
  const accessToken = generateToken(32);
  const accessTokenHash = hashToken(accessToken);

  const base = appBaseUrl().replace(/\/$/, '');
  const accessUrl = `${base}/acesso?token=${accessToken}`;

  const { credits, days } = getPlanSpecs(input.plan);
  const expiresAt = new Date(Date.now() + days * 24 * 60 * 60 * 1000);

  // Idempotência: se a ordem já tem credencial ativa, retorna ela
  const existing = await prisma.accessCredentials.findFirst({
    where: { orderId: input.orderId, status: 'active' },
  });
  if (existing) {
    return {
      credentialId: existing.id,
      username: existing.username,
      temporaryPassword: null,
      accessToken,
      accessUrl: existing.accessUrl || accessUrl,
      licenseKey: existing.licenseKey || 'FV-PENDING',
      credits: existing.credits || credits,
      courseUrl: existing.courseUrl || courseUrl(),
      colabUrl: colabUrl(),
      expiresAt: existing.expiresAt || expiresAt,
    };
  }

  // 1. Gera a Chave de Licença oficial Forja Viral
  const licenseKey = generateLicenseKey();

  // 2. Registra automaticamente no Servidor PostgreSQL do Railway!
  try {
    const srvRes = await createLicenseOnServer({
      licenseKey,
      credits,
      days,
      plan: input.plan,
    });
    console.log(`[Provisioning] Chave ${licenseKey} registrada no Railway:`, srvRes.message);
  } catch (err: any) {
    console.error(`[Provisioning] Falha ao registrar chave no Railway:`, err?.message);
  }

  // 3. Salva no banco de dados local do site
  const credential = await prisma.accessCredentials.create({
    data: {
      customerId: input.customerId,
      orderId: input.orderId,
      subscriptionId: input.subscriptionId,
      username,
      passwordHash,
      accessTokenHash,
      accessUrl,
      railwayAppUrl: process.env.FORJA_LICENSE_SERVER_URL || 'https://forja-license-production.up.railway.app',
      licenseKey,
      credits,
      courseUrl: courseUrl(),
      status: 'active',
      expiresAt,
    },
  });

  return {
    credentialId: credential.id,
    username,
    temporaryPassword,
    accessToken,
    accessUrl,
    licenseKey,
    credits,
    courseUrl: courseUrl(),
    colabUrl: colabUrl(),
    expiresAt,
  };
}

export async function revokeCredential(credentialId: string, reason = 'manual'): Promise<void> {
  await prisma.accessCredentials.update({
    where: { id: credentialId },
    data: { status: 'revoked', updatedAt: new Date() },
  });
  await prisma.auditLog.create({
    data: {
      eventType: 'credential_revoked',
      orderId: undefined,
      message: `Credential ${credentialId} revogada: ${reason}`,
    },
  });
}

export async function regenerateCredential(credentialId: string): Promise<{ accessToken: string; licenseKey: string }> {
  const accessToken = generateToken(32);
  const accessTokenHash = hashToken(accessToken);
  const newLicenseKey = generateLicenseKey();

  const cred = await prisma.accessCredentials.findUnique({ where: { id: credentialId } });
  if (cred) {
    await createLicenseOnServer({
      licenseKey: newLicenseKey,
      credits: cred.credits || 100,
      days: 30,
      plan: 'regenerated',
    });
  }

  await prisma.accessCredentials.update({
    where: { id: credentialId },
    data: {
      accessTokenHash,
      licenseKey: newLicenseKey,
      updatedAt: new Date(),
    },
  });

  return { accessToken, licenseKey: newLicenseKey };
}