import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Sun, Moon, MonitorPlay } from 'lucide-react';
import './Layout.css';
import AnimatedNav from './AnimatedNav';
import SwipeBack from './SwipeBack';

const Layout = ({ children }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isHeaderHidden, setIsHeaderHidden] = useState(false);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      // Update scrolled state for glass effect
      setIsScrolled(currentScrollY > 20);

      // Hide/show header based on scroll position
      if (currentScrollY > 50) {
        // Past 50px - hide header
        setIsHeaderHidden(true);
      } else if (currentScrollY <= 0) {
        // At the very top - show header
        setIsHeaderHidden(false);
      }

      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  // Sync theme with document element
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <div className={`app-layout ${isDark ? 'dark' : ''}`}>
      <SwipeBack />
      <header className={`site-header ${isScrolled ? 'scrolled glass' : ''} ${isHeaderHidden ? 'header-hidden' : ''}`}>
        <div className="container header-content">
          <Link to="/" className="logo">
            <div className="logo-icon-wrapper">
              <MonitorPlay size={24} color="var(--color-bg-card)" />
            </div>
            <div className="logo-text">
              <span className="brand">NH</span>
              <span className="dept">방송운영단</span>
            </div>
          </Link>

          {/* Desktop Navigation - Animated */}
          <div className="desktop-nav-wrapper">
            <AnimatedNav currentPath={location.pathname} />
          </div>

          {/* Mobile Navigation - Hidden on desktop via CSS */}
          <nav className={`main-nav mobile-only ${isMobileMenuOpen ? 'active' : ''}`}>
            <Link to="/" onClick={() => setIsMobileMenuOpen(false)} className={location.pathname === '/' ? 'active' : ''}>HOME</Link>
            <Link to="/about" onClick={() => setIsMobileMenuOpen(false)} className={location.pathname === '/about' ? 'active' : ''}>소개</Link>
            <Link to="/guide" onClick={() => setIsMobileMenuOpen(false)} className={location.pathname === '/guide' ? 'active' : ''}>이용안내</Link>
            <Link to="/facilities" onClick={() => setIsMobileMenuOpen(false)} className={location.pathname === '/facilities' ? 'active' : ''}>시설안내</Link>
            <Link to="/status" onClick={() => setIsMobileMenuOpen(false)} className={location.pathname === '/status' ? 'active' : ''}>장비현황</Link>
            <Link to="/schedule" onClick={() => setIsMobileMenuOpen(false)} className={location.pathname === '/schedule' ? 'active' : ''}>일정</Link>
          </nav>

          <div className="header-actions">
            <button onClick={toggleTheme} className="icon-btn" aria-label="Toggle Theme">
              {isDark ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button
              className="mobile-menu-btn"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        {children}
      </main>

      <footer className="site-footer">
        <div className="container footer-content">
          <div className="footer-info">
            <h3>NH 방송운영단</h3>
            <p>최고의 방송 환경과 시설을 제공합니다.</p>
          </div>
          <div className="footer-links">
            <span>© 2026 NH Broadcasting Operation.</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
