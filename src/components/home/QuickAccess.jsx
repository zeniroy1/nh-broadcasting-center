import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mic2, Users, Monitor, Coffee } from 'lucide-react';
import './QuickAccess.css';

const categories = [
    {
        id: 'auditorium',
        title: '대강당',
        icon: <Mic2 size={32} />,
        desc: '대규모 행사 및 세미나',
        color: '#4361ee'
    },
    {
        id: 'conference',
        title: '회의실',
        icon: <Users size={32} />,
        desc: '중/소규모 회의 공간',
        color: '#3a0ca3'
    },
    {
        id: 'studio',
        title: '화상회의실',
        icon: <Monitor size={32} />,
        desc: '최신 화상 장비 완비',
        color: '#7209b7'
    },
    {
        id: 'amenities',
        title: '편의시설',
        icon: <Coffee size={32} />,
        desc: '식당 및 휴게 공간',
        color: '#f72585'
    }
];

const QuickAccess = () => {
    return (
        <section className="quick-access-section">
            <div className="container">
                <div className="section-header">
                    <h2>주요 시설 바로가기</h2>
                    <p>원하시는 공간을 빠르게 찾아보세요.</p>
                </div>

                <div className="cards-grid">
                    {categories.map((cat, index) => (
                        <motion.div
                            key={cat.id}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Link to={`/facilities?type=${cat.id}`} className="access-card">
                                <div className="card-icon" style={{ backgroundColor: `${cat.color}20`, color: cat.color }}>
                                    {cat.icon}
                                </div>
                                <h3>{cat.title}</h3>
                                <p>{cat.desc}</p>
                                <div className="card-arrow">→</div>
                            </Link>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default QuickAccess;
