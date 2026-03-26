import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, MapPin } from 'lucide-react';
import './FacilityCard.css';

const FacilityCard = ({ facility, onClick, index = 0 }) => {
    const [currentImageIndex, setCurrentImageIndex] = React.useState(0);
    const [isHovered, setIsHovered] = React.useState(false);
    const hasImages = facility.images && facility.images.length > 0;

    React.useEffect(() => {
        if (!hasImages) return;

        const interval = setInterval(() => {
            setCurrentImageIndex((prev) => (prev + 1) % facility.images.length);
        }, 5000);

        return () => clearInterval(interval);
    }, [hasImages, facility.images]);

    return (
        <motion.div
            className="facility-card-wrapper"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <motion.div
                className={`facility-card ${isHovered ? 'card-glow' : ''}`}
                layout
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{
                    duration: 0.25,
                    ease: "easeOut"
                }}
                whileHover={{
                    scale: 1.03,
                    y: -8,
                    boxShadow: "0px 20px 40px rgba(0,53,148,0.2)"
                }}
                onClick={() => onClick(facility)}
            >
                <div className="card-shimmer" />
                <div className="card-image-wrapper">
                    <AnimatePresence mode="popLayout">
                        <motion.img
                            key={hasImages ? facility.images[currentImageIndex] : facility.image}
                            src={hasImages ? facility.images[currentImageIndex] : facility.image}
                            alt={facility.name}
                            className="card-image"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 1 }}
                        />
                    </AnimatePresence>
                    <div className="card-overlay">
                        <span className="view-details">상세보기</span>
                    </div>
                </div>
                <div className="card-content">
                    <div className="card-header">
                        <h3>{facility.name}</h3>
                        <span className={`category-tag ${facility.category}`}>
                            {facility.category === 'meeting' ? '회의' :
                                facility.category === 'amenities' ? '편의' : '운영'}
                        </span>
                    </div>
                    <p className="card-desc">{facility.description}</p>
                    <div className="card-meta">
                        <div className="meta-item">
                            <Users size={16} />
                            <span>{facility.capacity}</span>
                        </div>
                        <div className="meta-item">
                            <MapPin size={16} />
                            <span>{facility.location}</span>
                        </div>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
};

export default FacilityCard;
