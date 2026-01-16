import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * SwipeBack Component
 * 
 * Enables swipe-from-left-edge gesture to navigate back,
 * similar to iOS/Android native behavior.
 * Only active on touch devices.
 */
const SwipeBack = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const isSwiping = useRef(false);

  useEffect(() => {
    const EDGE_THRESHOLD = 20; // Narrower edge start
    const MIN_SWIPE_DISTANCE = 100; // More intentional swipe
    const MAX_VERTICAL_RATIO = 0.5; // X must move more than Y

    const handleTouchStart = (e) => {
      const touch = e.touches[0];
      // Only start if touch is near the left edge
      if (touch.clientX <= EDGE_THRESHOLD) {
        touchStartX.current = touch.clientX;
        touchStartY.current = touch.clientY;
        isSwiping.current = true;
      }
    };

    const handleTouchMove = (e) => {
      if (!isSwiping.current) return;
      // Prevent horizontal scrolling when swiping back from edge
      if (Math.abs(e.touches[0].clientX - touchStartX.current) > 10) {
        // Optional: stop propagation if needed
      }
    };

    const handleTouchEnd = (e) => {
      if (!isSwiping.current) return;

      const touch = e.changedTouches[0];
      const deltaX = touch.clientX - touchStartX.current;
      const deltaY = Math.abs(touch.clientY - touchStartY.current);

      // Must be a horizontal-ish swipe with enough distance
      if (deltaX >= MIN_SWIPE_DISTANCE && (deltaY / deltaX) < MAX_VERTICAL_RATIO) {
        // Prevent going back from home page
        if (location.pathname !== '/') {
          navigate(-1);
        }
      }
      isSwiping.current = false;
    };

    if ('ontouchstart' in window) {
      document.addEventListener('touchstart', handleTouchStart, { passive: true });
      document.addEventListener('touchmove', handleTouchMove, { passive: true });
      document.addEventListener('touchend', handleTouchEnd, { passive: true });
    }

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [navigate, location.pathname]);

  return null;
};

export default SwipeBack;
