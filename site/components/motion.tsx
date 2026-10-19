// Lightweight motion wrapper using Tailwind animation classes.
import { cn } from '@/lib/utils';

export function FadeIn({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('animate-fade-in', className)}>{children}</div>;
}

export function FadeInStagger({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('space-y-6', className)}>{children}</div>;
}

export function FadeInItem({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('animate-slide-up', className)}>{children}</div>;
}

export function Pulse({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('animate-pulse-slow', className)}>{children}</div>;
}