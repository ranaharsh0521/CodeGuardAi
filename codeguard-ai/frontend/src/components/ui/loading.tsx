import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullScreen?: boolean;
}

export function LoadingSpinner({ size = 'md', text, fullScreen = false }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center space-y-3">
      <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-500`} />
      {text && (
        <p className="text-gray-400 text-sm font-medium">{text}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-gray-950 flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}

export function PageLoading({ text = "Loading..." }: { text?: string }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <LoadingSpinner size="lg" text={text} />
    </div>
  );
}