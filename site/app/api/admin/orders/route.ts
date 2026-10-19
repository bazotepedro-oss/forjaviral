// GET /api/admin/orders
import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { prisma } from '@/lib/db';

export async function GET() {
  const admin = await verifyAdminRequest();
  if (!admin) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const orders = await prisma.order.findMany({
    include: { customer: true, plan: true },
    orderBy: { createdAt: 'desc' },
    take: 200,
  });
  return NextResponse.json({ orders });
}