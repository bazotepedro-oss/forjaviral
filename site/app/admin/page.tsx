import { redirect } from 'next/navigation';
import { prisma } from '@/lib/db';
import { AdminShell } from '@/components/admin-shell';
import { listLicensesFromServer } from '@/lib/license-server';
import { verifyAdminRequest } from '@/lib/auth';
import { syncAbacatePay } from '@/lib/sync-abacatepay';

export const revalidate = 0;

interface PageProps {
  searchParams?: { token?: string };
}

export default async function AdminPage({ searchParams }: PageProps) {
  const urlToken = searchParams?.token;
  const session = await verifyAdminRequest(urlToken);

  if (!session) {
    redirect('/admin/login');
  }

  // Sincroniza pagamentos da AbacatePay (v2) automaticamente com Railway
  await syncAbacatePay().catch((err) => console.error('Erro na auto-sincronização:', err));

  const [orders, subscriptions, customers, credentials, events, railwayLicenses] = await Promise.all([
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
    listLicensesFromServer(),
  ]);

  return (
    <AdminShell
      orders={orders}
      subscriptions={subscriptions}
      customers={customers}
      credentials={credentials}
      events={events}
      railwayLicenses={railwayLicenses}
    />
  );
}