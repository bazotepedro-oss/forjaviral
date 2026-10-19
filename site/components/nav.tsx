import Link from 'next/link';
import { cn } from '@/lib/utils';

interface NavProps {
  items: { label: string; href: string }[];
  className?: string;
}

export function Nav({ items, className }: NavProps) {
  return (
    <nav className={cn('flex items-center gap-6 text-sm text-text-secondary', className)}>
      {items.map((item) => (
        <Link key={item.href} href={item.href} className="transition-colors hover:text-text-primary">
          {item.label}
        </Link>
      ))}
    </nav>
  );
}