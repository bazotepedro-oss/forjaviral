import * as React from 'react';
import { cn } from '@/lib/utils';

export function Badge({ children, variant = 'default', className }: { children: React.ReactNode; variant?: 'default' | 'brand' | 'success' | 'outline'; className?: string }) {
  const styles = {
    default: 'bg-surface text-text-secondary border-white/10',
    brand: 'bg-brand/15 text-brand-soft border-brand/30',
    success: 'bg-success/15 text-success border-success/30',
    outline: 'bg-transparent text-text-secondary border-white/10',
  };
  return (
    <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium', styles[variant], className)}>
      {children}
    </span>
  );
}