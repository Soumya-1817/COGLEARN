import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warning' | 'danger' | 'success';
  title?: string;
  onClose?: () => void;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  className,
  onClose,
  ...props
}) => {
  const configs = {
    info: {
      bg: 'bg-sky-50 text-sky-800 border-sky-200',
      icon: <Info className="h-5 w-5 text-sky-600 shrink-0 mt-0.5" />,
    },
    warning: {
      bg: 'bg-amber-50 text-amber-800 border-amber-200',
      icon: <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />,
    },
    danger: {
      bg: 'bg-red-50 text-red-800 border-red-200',
      icon: <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />,
    },
    success: {
      bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      icon: <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />,
    },
  };

  const current = configs[variant];

  return (
    <div
      role="alert"
      className={cn('relative flex gap-3 rounded-xl border p-4 text-sm', current.bg, className)}
      {...props}
    >
      {current.icon}
      <div className="flex-1">
        {title && <h5 className="font-semibold text-sm mb-1 leading-none">{title}</h5>}
        <div className="text-sm opacity-90 leading-relaxed">{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="rounded-lg p-1 text-slate-400 hover:text-slate-600 transition-colors"
          aria-label="Dismiss alert"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

export default Alert;
