import { prisma } from './db';
import {
  listLicensesFromServer,
  addCreditsOnServer,
  createLicenseOnServer,
} from './license-server';
import { provision } from './provisioning';
import { sendRechargeEmail } from './email';

/**
 * Sincroniza pagamentos da AbacatePay (v2) diretamente com o banco local e Railway.
 * Funciona mesmo em localhost sem precisar de webhook externo!
 */
export async function syncAbacatePay(): Promise<{ synced: number; processed: string[] }> {
  const apiKey = process.env.ABACATEPAY_API_KEY;
  if (!apiKey) return { synced: 0, processed: [] };

  try {
    const res = await fetch('https://api.abacatepay.com/v2/checkouts/list', {
      headers: { Authorization: `Bearer ${apiKey}` },
      cache: 'no-store',
    });

    if (!res.ok) return { synced: 0, processed: [] };
    const json = await res.json();
    const checkouts = json.data || [];

    const processed: string[] = [];
    const railwayLicenses = await listLicensesFromServer();

    for (const c of checkouts) {
      if (c.status !== 'PAID') continue;

      const order = await prisma.order.findFirst({
        where: {
          OR: [
            { abacateCheckoutId: c.id },
            { id: c.metadata?.orderId },
          ],
        },
        include: { customer: true, plan: true },
      });

      if (!order || order.status === 'paid') continue;

      // 1. Marca como pago
      await prisma.order.update({
        where: { id: order.id },
        data: { status: 'paid', paidAt: new Date(c.updatedAt || Date.now()) },
      });

      const meta = (order.metadata as any) || c.metadata || {};
      const isRecharge = meta.isRecharge === true || meta.isRecharge === 'true';

      if (isRecharge && meta.licenseKey && meta.creditsToAdd) {
        const credits = Number(meta.creditsToAdd);
        const key = String(meta.licenseKey).trim();
        const existsOnRailway = railwayLicenses.some(
          (l) => l.license_key.toUpperCase() === key.toUpperCase()
        );

        if (existsOnRailway) {
          await addCreditsOnServer(key, credits);
          console.log(`[Sync AbacatePay] +${credits} créditos adicionados à chave existente ${key}`);
        } else {
          await createLicenseOnServer({
            licenseKey: key,
            credits,
            days: 365,
            plan: meta.packageSlug || 'recarga',
          });
          console.log(`[Sync AbacatePay] Nova chave ${key} criada no Railway com ${credits} créditos`);
        }

        // Atualiza ou cria a credencial no banco local
        await prisma.accessCredentials.upsert({
          where: { id: `cred_${order.id}` },
          update: {
            credits,
            licenseKey: key,
            status: 'active',
          },
          create: {
            id: `cred_${order.id}`,
            customerId: order.customerId,
            orderId: order.id,
            username: order.customer.email.split('@')[0],
            accessUrl: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/acesso`,
            licenseKey: key,
            credits,
            status: 'active',
            expiresAt: new Date(Date.now() + 365 * 86400000),
          },
        });

        // Envia e-mail de recarga confirmada
        await sendRechargeEmail({
          to: order.customer.email,
          name: order.customer.name,
          licenseKey: key,
          creditsAdded: credits,
        }).catch((err) => console.error('[Sync AbacatePay] Falha ao enviar e-mail de recarga:', err));
      } else if (!isRecharge) {
        // Compra de plano novo
        let subscription = await prisma.subscription.findFirst({
          where: { customerId: order.customerId, planId: order.planId, status: 'active' },
        });

        if (!subscription) {
          subscription = await prisma.subscription.create({
            data: {
              customerId: order.customerId,
              planId: order.planId,
              status: 'active',
              provider: 'AbacatePay',
              orderId: order.id,
            },
          });
        }

        await provision({
          customerId: order.customerId,
          orderId: order.id,
          subscriptionId: subscription.id,
          email: order.customer.email,
          plan: order.plan.slug,
        });
      }

      processed.push(c.id);
    }

    return { synced: processed.length, processed };
  } catch (err: any) {
    console.error('[Sync AbacatePay] Erro ao sincronizar:', err?.message);
    return { synced: 0, processed: [] };
  }
}
