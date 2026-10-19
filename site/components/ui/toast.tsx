import { cn } from '@/lib/utils';

interface ToastProps {
  message: string;
  variant?: 'success' | 'error' | 'info';
  onDismiss?: () => void;
}

export function Toast({ message, variant = 'info', onDismiss }: ToastProps) {
  const styles = {
    success: 'border-success/30 bg-success/10 text-success',
    error: 'border-error/30 bg-error/10 text-error',
    info: 'border-brand/30 bg-brand/10 text-brand-soft',
  };
  return (
    <div className={cn('flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm shadow-card', styles[variant])}>
      <span>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="text-current hover:opacity-70" aria-label="Fechar">
          ✕
        </button>
      )}
    </div>
  );
}