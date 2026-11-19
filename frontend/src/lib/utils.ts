import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, isPast, parseISO } from 'date-fns';
import { RiskZone, DominantCognitiveState } from '@/types';

/**
 * Merges Tailwind classes conditionally and safely
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format an ISO date string or Date object into human-readable date
 */
export function formatDate(date: string | Date | null | undefined, pattern: string = 'MMM d, yyyy'): string {
  if (!date) return 'N/A';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return format(d, pattern);
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format datetime string
 */
export function formatDateTime(date: string | Date | null | undefined): string {
  return formatDate(date, 'MMM d, yyyy h:mm a');
}

/**
 * Relative distance to now (e.g., "in 2 days" or "3 hours ago")
 */
export function formatRelative(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  try {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    return 'Invalid date';
  }
}

/**
 * Check if a date string is past due
 */
export function checkIsOverdue(dueDate: string | Date | null | undefined): boolean {
  if (!dueDate) return false;
  try {
    const d = typeof dueDate === 'string' ? parseISO(dueDate) : dueDate;
    return isPast(d);
  } catch {
    return false;
  }
}

/**
 * Returns color classes for IORI risk zone
 */
export function getRiskZoneColor(zone: RiskZone): {
  text: string;
  bg: string;
  border: string;
  badge: string;
} {
  switch (zone) {
    case 'red':
      return {
        text: 'text-red-700',
        bg: 'bg-red-50',
        border: 'border-red-200',
        badge: 'bg-red-100 text-red-800 border-red-300',
      };
    case 'yellow':
      return {
        text: 'text-amber-700',
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        badge: 'bg-amber-100 text-amber-800 border-amber-300',
      };
    case 'green':
    default:
      return {
        text: 'text-emerald-700',
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
      };
  }
}

/**
 * Determine risk zone from numeric IORI value
 * Formula thresholds:
 * green: IORI < 0.3
 * yellow: 0.3 <= IORI < 0.6
 * red: IORI >= 0.6
 */
export function getIoriRiskZone(value: number): RiskZone {
  if (value >= 0.6) return 'red';
  if (value >= 0.3) return 'yellow';
  return 'green';
}

/**
 * Cognitive state color mappings
 */
export function getDominantStateColor(state: DominantCognitiveState): {
  text: string;
  bg: string;
  border: string;
} {
  switch (state) {
    case 'flow':
      return { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' };
    case 'underload':
      return { text: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-200' };
    case 'fatigue':
      return { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' };
    case 'overload':
      return { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200' };
  }
}

/**
 * M/M/1 Queue Regime classification from rho
 * Underload: rho < 0.5
 * Flow: 0.5 <= rho < 0.8
 * Strain: 0.8 <= rho < 1.0
 * Overload: rho >= 1.0 (unstable)
 */
export function getRegimeFromRho(rho: number, isStable: boolean): 'underload' | 'flow' | 'strain' | 'overload' {
  if (!isStable || rho >= 1.0) return 'overload';
  if (rho >= 0.8) return 'strain';
  if (rho >= 0.5) return 'flow';
  return 'underload';
}
