import { prisma } from '@/lib/db';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { Hero } from '@/components/sections/hero';
import { ComoFunciona } from '@/components/sections/como-funciona';
import { Recursos } from '@/components/sections/recursos';
import { Depoimentos } from '@/components/sections/depoimentos';
import { PlanosSection } from '@/components/sections/planos-section';
import { FAQSection } from '@/components/sections/faq-section';
import { CTAFinal } from '@/components/sections/cta-final';

export const revalidate = 60;

export default async function HomePage() {
  const plans = await prisma.plan.findMany({ where: { active: true }, orderBy: { price: 'asc' } });

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <Hero />
      <ComoFunciona />
      <Recursos />
      <Depoimentos />
      <PlanosSection plans={plans} />
      <FAQSection />
      <CTAFinal />
      <Footer />
    </div>
  );
}