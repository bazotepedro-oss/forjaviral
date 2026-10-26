import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Fábrica de Cortes | Corte vídeos longos em virais com IA',
  description: 'Acesse a Fábrica de Cortes (fabricadecortes.com). Transforme vídeos longos em cortes prontos para TikTok, Reels e Shorts com IA.',
  openGraph: {
    title: 'Fábrica de Cortes (fabricadecortes.com)',
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