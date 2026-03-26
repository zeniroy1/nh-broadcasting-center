import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import './HeroSection.css';

const HeroSection = () => {
    return (
        <section className="hero-section">
            <div className="hero-background">
                <div className="gradient-overlay"></div>
                <div className="animated-shapes">
                    <div className="shape shape-1"></div>
                    <div className="shape shape-2"></div>
                    <div className="shape shape-3"></div>
                </div>
            </div>

            <div className="container hero-content">
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="hero-text-wrapper"
                >
                    <motion.span
                        className="hero-subtitle"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3, duration: 0.8 }}
                    >
                        Smart Broadcasting Solution
                    </motion.span>
                    <h1 className="hero-title">
                        NH <span className="highlight">방송운영단</span>
                    </h1>
                    <p className="hero-description">
                        최첨단 방송 시설과 스마트한 운영 시스템으로<br />
                        최고의 커뮤니케이션 환경을 제공합니다.
                    </p>

                    <div className="hero-actions">
                        <Link to="/facilities" className="btn-primary">시설 보기</Link>
                        <Link to="/guide" className="btn-secondary">이용 안내</Link>
                    </div>
                </motion.div>
            </div>

            <motion.div
                className="scroll-indicator"
                animate={{ y: [0, 10, 0] }}
                transition={{ repeat: Infinity, duration: 2 }}
            >
                <ChevronDown size={32} />
            </motion.div>
        </section>
    );
};

export default HeroSection;
