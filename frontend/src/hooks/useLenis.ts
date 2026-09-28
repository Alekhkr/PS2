import { useEffect, useRef } from 'react';
import Lenis from 'lenis';

export function useLenis(onScroll?: (progress: number, velocity: number) => void) {
  const lenisRef = useRef<Lenis | null>(null);

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 1.5,
    });
    lenisRef.current = lenis;

    const handleScroll = (e: { progress: number; velocity: number }) => {
      onScroll?.(e.progress, e.velocity);
    };

    lenis.on('scroll', handleScroll);

    let rafId: number;
    function raf(time: number) {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    }
    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.off('scroll', handleScroll);
      lenis.destroy();
    };
  }, [onScroll]);

  return lenisRef;
}
