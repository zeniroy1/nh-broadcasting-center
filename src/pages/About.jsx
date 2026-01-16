import React from 'react';
import { motion } from 'framer-motion';
import PageTransition from '../components/layout/PageTransition';
import './About.css';
import WaveDecoration from '../components/layout/WaveDecoration';

const AnimatedGradientText = ({ text }) => {
    // Split text into letters
    const letters = Array.from(text);

    const container = {
        hidden: { opacity: 0 },
        visible: (i = 1) => ({
            opacity: 1,
            transition: { staggerChildren: 0.05, delayChildren: 0.04 * i },
        }),
        hover: {
            transition: { staggerChildren: 0.05 }
        }
    };

    const child = {
        visible: {
            opacity: 1,
            y: 0,
            transition: {
                type: "spring",
                damping: 12,
                stiffness: 100,
            },
        },
        hidden: {
            opacity: 0,
            y: 20,
            transition: {
                type: "spring",
                damping: 12,
                stiffness: 100,
            },
        },
        hover: {
            y: [-5, -20, 0], // More dramatic jump
            scale: [1, 1.3, 1], // Pulse scale
            rotate: [0, -10, 10, 0], // Wiggle
            transition: {
                duration: 0.6,
                ease: "easeInOut",
                repeat: 0
            }
        }
    };

    return (
        <motion.div
            style={{
                overflow: "visible",
                display: "flex",
                justifyContent: "center",
                cursor: "pointer",
                padding: "20px" // Increased padding for dramatic moves
            }}
            variants={container}
            initial="hidden"
            animate="visible"
            whileHover="hover"
        >
            {letters.map((letter, index) => (
                <motion.span
                    variants={child}
                    key={index}
                    className="animated-gradient-char"
                    style={{
                        marginRight: letter === " " ? "0.8rem" : "0px",
                    }}
                >
                    {letter}
                </motion.span>
            ))}
        </motion.div>
    );
};

const About = () => {
    return (
        <PageTransition>
            <div className="about-page">
                <section className="about-hero">
                    <div className="container">
                        <AnimatedGradientText text="방송운영단 안내" />
                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            NH농협의 목소리를 세상에 전하는 중심
                        </motion.p>
                    </div>
                </section>

                <section className="about-content container">
                    <div className="about-grid">
                        <motion.div
                            className="about-card"
                            initial={{ opacity: 0, x: -50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                        >
                            <h2>Mission</h2>
                            <p>
                                최상의 방송 품질과 안정적인 운영 시스템을 통해<br />
                                완벽한 행사 지원 및 정보 공유를 지원합니다.
                            </p>
                        </motion.div>

                        <motion.div
                            className="about-card"
                            initial={{ opacity: 0, x: 50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                        >
                            <h2>Vision</h2>
                            <p>
                                디지털 혁신을 선도하는<br />
                                스마트 방송 커뮤니케이션 허브
                            </p>
                        </motion.div>
                    </div>

                    <div className="organization-chart">
                        <h2>조직 구성</h2>
                        <div className="chart-wrapper">
                            {/* Simple visual representation of hierarchy */}
                            <div className="chart-node root">방송운영단장</div>
                            <div className="chart-lines"></div>
                            <div className="chart-row">
                                <div className="chart-node">기술지원</div>
                            </div>
                        </div>
                    </div>
                </section>
                <WaveDecoration />
            </div>
        </PageTransition>
    );
};

export default About;
