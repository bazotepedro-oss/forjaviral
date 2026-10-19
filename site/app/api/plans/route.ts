// GET /api/plans — return active plans
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';

export async function GET() {
  const plans = await prisma.plan.findMany({
    where: { active: true },
    orderBy: { slug: 'asc' },
  });
  return NextResponse.json({ plans });
}