// POST /api/admin/orders/[id]/activate — manual activation with audit
import { NextResponse } from 'next/server';
import { verifyAdminRequest } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { provision } from '@/lib/provisioning';

export async function POST(req: Request, { params }: { params: { id: string } }) {
  const admin = await verifyAdminRequest();
  if (!admin) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const order = await prisma.order.findUnique({ where: { id: params.id } });
  if (!order) return NextResponse.json({ error: 'not found' }, { status: 404 });

  await prisma.order.update({ where: { id: order.id }, data: { status: 'paid', paidAt: new Date() } });

  let subscription = await prisma.subscription.findFirst({
    where: { customerId: order.customerId, planId: order.planId, status: 'active' },
  });
  if (!subscription) {
    subscription = await prisma.subscription.create({
      data: { customerId: order.customerId, planId: order.planId, status: 'active', provider: 'manual' },
    });
  }

  const customer = await prisma.customer.findUnique({ where: { id: order.customerId } });
  const plan = await prisma.plan.findUnique({ where: { id: order.planId } });
  if (customer && plan) {
    await provision({
      customerId: customer.id,
      orderId: order.id,
      subscriptionId: subscription.id,
      email: customer.email,
      plan: plan.slug,
    });
  }

  await prisma.auditLog.create({
    data: { eventType: 'manual_activate', userId: admin.adminId, orderId: order.id, message: 'Ativação manual por admin' },
  });

  return NextResponse.json({ ok: true });
}