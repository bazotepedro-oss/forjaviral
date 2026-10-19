// GET /api/admin/credentials
import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { prisma } from '@/lib/db';

export async function GET() {
  const admin = await verifyAdminRequest();
  if (!admin) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const creds = await prisma.accessCredentials.findMany({
    include: { customer: true, order: true },
    orderBy: { createdAt: 'desc' },
    take: 200,
  });
  return NextResponse.json({ credentials: creds });
}