import { prisma } from '@/lib/db';
import { AdminShell } from '@/components/admin-shell';

export const revalidate = 0;

export default async function AdminPage() {
  const [orders, subscriptions, customers, credentials, events] = await Promise.all([
    prisma.order.findMany({ include: { customer: true, plan: true }, orderBy: { createdAt: 'desc' }, take: 50 }),
    prisma.subscription.findMany({ include: { customer: true, plan: true }, orderBy: { createdAt: 'desc' }, take: 50 }),
    prisma.customer.findMany({
      include: {
        orders: { include: { plan: true }, orderBy: { createdAt: 'desc' } },
        credentials: { orderBy: { createdAt: 'desc' } },
      },
      orderBy: { createdAt: 'desc' },
      take: 100,
    }),
    prisma.accessCredentials.findMany({ include: { customer: true, order: true }, orderBy: { createdAt: 'desc' }, take: 50 }),
    prisma.webhookEvent.findMany({ orderBy: { createdAt: 'desc' }, take: 50 }),
  ]);

  return (
    <AdminShell
      orders={orders}
      subscriptions={subscriptions}
      customers={customers}
      credentials={credentials}
      events={events}
    />
  );
}