// GET /api/access/[token] — validates one-time token and returns credentials.
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { verifyAccessLinkToken } from '@/lib/auth';

export async function GET(req: Request, { params }: { params: { token: string } }) {
  const claims = verifyAccessLinkToken(params.token);
  if (!claims) {
    return NextResponse.json({ error: 'token inválido ou expirado' }, { status: 401 });
  }

  const credential = await prisma.accessCredentials.findFirst({
    where: { orderId: claims.orderId, status: 'active' },
  });
  if (!credential) {
    return NextResponse.json({ error: 'acesso ainda não disponível' }, { status: 404 });
  }

  return NextResponse.json({
    username: credential.username,
    accessUrl: credential.accessUrl,
    status: credential.status,
    expiresAt: credential.expiresAt,
  });
}