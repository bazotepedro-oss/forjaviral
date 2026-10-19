import { prisma } from '@/lib/db';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';
import { FAQSection } from '@/components/sections/faq-section';

export const revalidate = 60;

export default function FAQPage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl px-4 py-20">
        <h1 className="font-display text-3xl font-bold text-text-primary md:text-4xl">
          Perguntas <span className="text-brand">frequentes</span>
        </h1>
        <div className="mt-10">
          <FAQSection />
        </div>
      </main>
      <Footer />
    </div>
  );
}