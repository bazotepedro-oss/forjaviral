import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Forja Viral | Corte vídeos longos em cortes virais com IA',
  description: 'Assine e receba acesso automático. Transforme vídeos longos em cortes prontos para TikTok, Reels e Shorts com IA.',
  openGraph: {
    title: 'Forja Viral',
    description: 'Cortes virais com IA em segundos.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <body className="min-h-screen bg-background text-text-primary font-sans antialiased">
        {children}
      </body>
    </html>
  );
}