// frontend/src/components/ui/Card.js
import { cn } from '@/lib/utils';

const Card = ({ 
  children, 
  className,
  padding = 'default',
  ...props 
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    default: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={cn(
        'bg-white rounded-lg border border-gray-200 shadow-sm',
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

const CardHeader = ({ children, className, ...props }) => (
  <div
    className={cn('border-b border-gray-200 pb-4 mb-4', className)}
    {...props}
  >
    {children}
  </div>
);

const CardTitle = ({ children, className, ...props }) => (
  <h3
    className={cn('text-lg font-medium text-gray-900', className)}
    {...props}
  >
    {children}
  </h3>
);

const CardContent = ({ children, className, ...props }) => (
  <div className={cn('', className)} {...props}>
    {children}
  </div>
);

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Content = CardContent;

export default Card;
