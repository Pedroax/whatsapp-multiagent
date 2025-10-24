/**
 * Badge que pisca para chamar atenção
 */
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface PulsingBadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'destructive' | 'outline' | 'secondary'
  className?: string
  pulse?: boolean
}

export function PulsingBadge({
  children,
  variant = 'destructive',
  className,
  pulse = true
}: PulsingBadgeProps) {
  return (
    <Badge
      variant={variant}
      className={cn(
        'relative',
        pulse && 'animate-pulse',
        className
      )}
    >
      {children}
      {pulse && (
        <span className="absolute -top-1 -right-1 w-3 h-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
        </span>
      )}
    </Badge>
  )
}
