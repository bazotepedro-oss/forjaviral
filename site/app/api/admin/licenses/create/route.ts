// POST /api/admin/licenses/create — Cria chave no Railway e opcionalmente cadastra no CRM do site
import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { createLicenseOnServer, generateLicenseKey } from '@/lib/license-server';
import { prisma } from '@/lib/db';
import { courseUrl, colabUrl } from '@/lib/provisioning';

export async function POST(req: Request) {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  let body: any;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'JSON inválido' }, { status: 400 });
  }

  const licenseKey = (body.licenseKey || generateLicenseKey()).trim().toUpperCase();
  const credits = Number(body.credits) || 100;
  const days = Number(body.days) || 30;
  const plan = (body.plan || 'pro').trim();
  const name = (body.name || '').trim();
  const email = (body.email || '').trim().toLowerCase();
  const phone = (body.phone || '').trim();

  // 1. Cria a licença no servidor Railway (PostgreSQL)
  const srvRes = await createLicenseOnServer({
    licenseKey,
    credits,
    days,
    plan,
  });

  if (!srvRes.ok) {
    return NextResponse.json({ error: srvRes.message }, { status: 502 });
  }

  // 2. Se informou nome e e-mail, cadastra/vincula no CRM local do site
  if (email && name) {
    let customer = await prisma.customer.findUnique({ where: { email } });
    if (!customer) {
      customer = await prisma.customer.create({
        data: { name, email, phone: phone || null },
      });
    } else if (phone && !customer.phone) {
      await prisma.customer.update({
        where: { id: customer.id },
        data: { phone },
      });
    }

    const expiresAt = new Date(Date.now() + days * 24 * 60 * 60 * 1000);
    const base = (process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000').replace(/\/$/, '');

    await prisma.accessCredentials.create({
      data: {
        customerId: customer.id,
        username: email.split('@')[0],
        licenseKey,
        credits,
        courseUrl: courseUrl(),
        accessUrl: `${base}/acesso`,
        status: 'active',
        expiresAt,
      },
    });
  }

  return NextResponse.json({
    ok: true,
    licenseKey,
    message: `Chave ${licenseKey} criada com sucesso no Railway e integrada ao CRM!`,
  });
}
