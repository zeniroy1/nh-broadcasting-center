import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu } from 'lucide-react';
import './AnimatedNav.css';

const navItems = [
    { path: '/', label: 'HOME' },
    { path: '/about', label: '소개' },
    { path: '/guide', label: '이용안내' },
    { path: '/facilities', label: '시설안내' },
    { path: '/status', label: '장비현황' },
    { path: '/schedule', label: '일정' },
];

const AnimatedNav = ({ currentPath }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div
            className="animated-nav-container"
            onMouseEnter={() => setIsOpen(true)}
            onMouseLeave={() => setIsOpen(false)}
        >
            <motion.div
                className="nav-trigger menu-item"
                animate={{
                    opacity: isOpen ? 0 : 1,
                    scale: isOpen ? 0.8 : 1
                }}
                transition={{ duration: 0.3 }}
            >
                <div className="trigger-content">
                    <Menu size={18} />
                    <span>MENU</span>
                </div>
            </motion.div>

            <div className="nav-items-wrapper">
                <AnimatePresence>
                    {isOpen && (
                        <motion.ul
                            className="nav-list"
                            initial="hidden"
                            animate="visible"
                            exit="hidden"
                            variants={{
                                hidden: { opacity: 0 },
                                visible: {
                                    opacity: 1,
                                    transition: {
                                        staggerChildren: 0.1,
                                        delayChildren: 0.1
                                    }
                                }
                            }}
                        >
                            {navItems.map((item, index) => (
                                <motion.li
                                    key={item.path}
                                    variants={{
                                        hidden: {
                                            opacity: 0,
                                            x: -20,
                                            rotateY: 45,
                                            scale: 0.9
                                        },
                                        visible: {
                                            opacity: 1,
                                            x: 0,
                                            rotateY: 0,
                                            scale: 1,
                                            transition: {
                                                type: 'spring',
                                                stiffness: 120,
                                                damping: 10
                                            }
                                        }
                                    }}
                                >
                                    <Link
                                        to={item.path}
                                        className={`menu-item ${currentPath === item.path ? 'active' : ''}`}
                                    >
                                        {item.label}
                                    </Link>
                                </motion.li>
                            ))}
                        </motion.ul>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default AnimatedNav;
