import { cn } from '@/lib/utils';

export function Container({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('mx-auto w-full max-w-6xl px-4', className)}>{children}</div>;
}

export function Section({ children, className, py = 'md' }: { children: React.ReactNode; className?: string; py?: 'sm' | 'md' | 'lg' }) {
  const pys = { sm: 'py-8', md: 'py-16', lg: 'py-24' };
  return <section className={cn(pys[py], className)}>{children}</section>;
}

export function Heading({ children, as: As = 'h2', className }: { children: React.ReactNode; as?: 'h1' | 'h2' | 'h3'; className?: string }) {
  return (
    <As className={cn('font-display text-3xl font-bold tracking-tight text-text-primary md:text-4xl lg:text-5xl', className)}>
      {children}
    </As>
  );
}

export function Subheading({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn('mt-4 text-lg text-text-secondary md:text-xl', className)}>{children}</p>;
}

export function GradientText({ children }: { children: React.ReactNode }) {
  return <span className="bg-gradient-to-r from-brand to-brand-soft bg-clip-text text-transparent">{children}</span>;
}

export function Divider({ className }: { className?: string }) {
  return <div className={cn('h-px w-full bg-border', className)} />;
}