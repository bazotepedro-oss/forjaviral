// GET /api/orders/[id]/status — returns order status + credentials if available.
// Protected by one-time token or email+orderId query.
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { verifyAccessLinkToken } from '@/lib/auth';

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const { searchParams } = new URL(req.url);
  const token = searchParams.get('token');
  const email = searchParams.get('email')?.toLowerCase();

  const order = await prisma.order.findUnique({ where: { id: params.id } });
  if (!order) return NextResponse.json({ error: 'not found' }, { status: 404 });

  // Authz: either token matches, or email matches the customer
  let authorized = false;
  if (token) {
    const claims = verifyAccessLinkToken(token);
    if (claims && claims.orderId === order.id) authorized = true;
  }
  if (email) {
    const customer = await prisma.customer.findUnique({ where: { id: order.customerId } });
    if (customer && customer.email.toLowerCase() === email) authorized = true;
  }
  if (!authorized) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const credentials = await prisma.accessCredentials.findFirst({
    where: { orderId: order.id, status: 'active' },
  });
  const subscription = await prisma.subscription.findFirst({
    where: { customerId: order.customerId, status: 'active' },
  });

  return NextResponse.json({
    order: { id: order.id, status: order.status, amount: order.amount, currency: order.currency, createdAt: order.createdAt },
    subscription: subscription ? { id: subscription.id, status: subscription.status } : null,
    credentials: credentials
      ? {
          id: credentials.id,
          username: credentials.username,
          accessUrl: credentials.accessUrl,
          status: credentials.status,
          expiresAt: credentials.expiresAt,
        }
      : null,
  });
}