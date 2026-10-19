import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { toggleLicenseOnServer } from '@/lib/license-server';

export async function POST(req: Request) {
  const auth = await verifyAdminRequest();
  if (!auth) return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });

  const { licenseKey } = await req.json();
  if (!licenseKey) return NextResponse.json({ error: 'Chave obrigatória' }, { status: 400 });

  const res = await toggleLicenseOnServer(licenseKey);
  return NextResponse.json(res);
}
