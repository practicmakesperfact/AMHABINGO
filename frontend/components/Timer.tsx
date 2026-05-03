'use client';

import { useEffect, useState } from 'react';

interface TimerProps {
  seconds: number;
  label?: string;
  onComplete?: () => void;
}

export default function Timer({ seconds, label = 'Time Remaining', onComplete }: TimerProps) {
  const [timeLeft, setTimeLeft] = useState(seconds);

  useEffect(() => {
    setTimeLeft(seconds);
  }, [seconds]);

  useEffect(() => {
    if (timeLeft <= 0) {
      onComplete?.();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          onComplete?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, onComplete]);

  const minutes = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  const isUrgent = timeLeft <= 10;

  return (
    <div className="text-center">
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className={`
        text-4xl font-bold
        ${isUrgent ? 'text-red-500 animate-pulse' : 'text-white'}
      `}>
        {minutes}:{secs.toString().padStart(2, '0')}
      </div>
    </div>
  );
}
