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
    const EDGE_THRESHOLD = 30; // Starting swipe must be within 30px from left edge
    const MIN_SWIPE_DISTANCE = 80; // Minimum swipe distance to trigger back
    const MAX_VERTICAL_DISTANCE = 100; // Cancel if vertical movement is too much

    const handleTouchStart = (e) => {
      const touch = e.touches[0];
      
      // Only detect swipe starting from left edge
      if (touch.clientX <= EDGE_THRESHOLD) {
        touchStartX.current = touch.clientX;
        touchStartY.current = touch.clientY;
        isSwiping.current = true;
      }
    };

    const handleTouchMove = (e) => {
      // Optional: Add visual feedback during swipe
      // Could add an overlay or animation here
    };

    const handleTouchEnd = (e) => {
      if (!isSwiping.current) return;

      const touch = e.changedTouches[0];
      const deltaX = touch.clientX - touchStartX.current;
      const deltaY = Math.abs(touch.clientY - touchStartY.current);

      // Check if swipe is valid (horizontal swipe to the right)
      if (deltaX >= MIN_SWIPE_DISTANCE && deltaY < MAX_VERTICAL_DISTANCE) {
        // Don't go back if we're on the home page
        if (location.pathname !== '/') {
          navigate(-1);
        }
      }

      isSwiping.current = false;
    };

    // Only add listeners on touch devices
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

  // This component doesn't render anything visible
  return null;
};

export default SwipeBack;
