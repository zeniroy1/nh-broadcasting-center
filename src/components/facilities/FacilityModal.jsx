import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Users, MapPin, CheckCircle, ChevronRight, ChevronLeft, ArrowLeft, FileText, Download } from 'lucide-react';
import './FacilityModal.css';

const FacilityModal = ({ facility, onClose }) => {
    const [view, setView] = useState('main'); // 'main' or 'sub-detail'
    const [selectedSubItem, setSelectedSubItem] = useState(null);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [direction, setDirection] = useState(0);
    const [isZoomed, setIsZoomed] = useState(false);
    const [isDragging, setIsDragging] = useState(false);

    const variants = {
        enter: (direction) => ({
            x: direction > 0 ? 1000 : -1000,
            opacity: 0
        }),
        center: {
            zIndex: 1,
            x: 0,
            opacity: 1
        },
        exit: (direction) => ({
            zIndex: 0,
            x: direction < 0 ? 1000 : -1000,
            opacity: 0
        })
    };

    const swipeConfidenceThreshold = 10000;
    const swipePower = (offset, velocity) => {
        return Math.abs(offset) * velocity;
    };

    const paginate = (newDirection) => {
        setDirection(newDirection);
        if (!facility?.images) return;

        setCurrentImageIndex((prev) => {
            let nextIndex = prev + newDirection;
            if (nextIndex < 0) nextIndex = facility.images.length - 1;
            if (nextIndex >= facility.images.length) nextIndex = 0;
            return nextIndex;
        });
    };

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (view !== 'main' || !facility?.images || facility.images.length <= 1) return;

            if (e.key === 'ArrowLeft') {
                paginate(-1);
            } else if (e.key === 'ArrowRight') {
                paginate(1);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [view, facility, paginate]);

    // Lock body scroll when modal is open
    useEffect(() => {
        // Save current scroll position and lock body
        const scrollY = window.scrollY;
        document.body.style.position = 'fixed';
        document.body.style.top = `-${scrollY}px`;
        document.body.style.left = '0';
        document.body.style.right = '0';
        document.body.style.overflow = 'hidden';

        // Cleanup: restore scroll position when modal closes
        return () => {
            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.left = '';
            document.body.style.right = '';
            document.body.style.overflow = '';
            window.scrollTo(0, scrollY);
        };
    }, []);

    if (!facility) return null;

    const handleSubItemClick = (item) => {
        setSelectedSubItem(item);
        setView('sub-detail');
    };

    const handleBack = () => {
        setView('main');
        setSelectedSubItem(null);
    };

    return (
        <AnimatePresence>
            <motion.div
                className="modal-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                onClick={onClose}
            >
                <motion.div
                    className="modal-content"
                    initial={{ y: 50, opacity: 0, scale: 0.96 }}
                    animate={{ y: 0, opacity: 1, scale: 1 }}
                    exit={{ y: 30, opacity: 0, scale: 0.98 }}
                    transition={{
                        type: "spring",
                        stiffness: 100,
                        damping: 16,
                        mass: 1.2,
                        opacity: { duration: 0.5 }
                    }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <button className="close-btn" onClick={onClose}>
                        <X size={24} />
                    </button>

                    <AnimatePresence mode="wait">
                        {view === 'main' ? (
                            <motion.div
                                key="main"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="modal-main-view"
                            >
                                <div className="modal-image-container">
                                    <div className="carousel-container">
                                        <AnimatePresence initial={false} custom={direction}>
                                            <motion.img
                                                key={currentImageIndex}
                                                src={facility.images ? facility.images[currentImageIndex] : facility.image}
                                                alt={facility.name}
                                                custom={direction}
                                                variants={variants}
                                                initial="enter"
                                                animate="center"
                                                exit="exit"
                                                transition={{
                                                    x: { type: "spring", stiffness: 100, damping: 20 },
                                                    opacity: { duration: 0.5 }
                                                }}
                                                drag="x"
                                                dragConstraints={{ left: 0, right: 0 }}
                                                dragElastic={1}
                                                onDragStart={() => setIsDragging(true)}
                                                onDragEnd={(e, { offset, velocity }) => {
                                                    const swipe = swipePower(offset.x, velocity.x);

                                                    if (swipe < -swipeConfidenceThreshold) {
                                                        paginate(1);
                                                    } else if (swipe > swipeConfidenceThreshold) {
                                                        paginate(-1);
                                                    }

                                                    // Small delay to reset dragging state so click doesn't fire immediately
                                                    setTimeout(() => setIsDragging(false), 100);
                                                }}
                                                onClick={() => {
                                                    if (!isDragging) {
                                                        setIsZoomed(true);
                                                    }
                                                }}
                                                className="carousel-image"
                                            />
                                        </AnimatePresence>

                                        {facility.images && facility.images.length > 1 && (
                                            <>
                                                <button className="carousel-btn prev" onClick={(e) => { e.stopPropagation(); paginate(-1); }}>
                                                    <ChevronLeft size={24} />
                                                </button>
                                                <button className="carousel-btn next" onClick={(e) => { e.stopPropagation(); paginate(1); }}>
                                                    <ChevronRight size={24} />
                                                </button>
                                                <div className="carousel-indicators">
                                                    {facility.images.map((_, idx) => (
                                                        <div
                                                            key={idx}
                                                            className={`indicator ${idx === currentImageIndex ? 'active' : ''}`}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setDirection(idx > currentImageIndex ? 1 : -1);
                                                                setCurrentImageIndex(idx);
                                                            }}
                                                        />
                                                    ))}
                                                </div>
                                            </>
                                        )}
                                    </div>
                                    <div className="modal-title-overlay">
                                        <h2>{facility.name}</h2>
                                        <span className="modal-category">{facility.category}</span>
                                    </div>
                                </div>

                                <div className="modal-body">
                                    <div className="modal-info-grid">
                                        <div className="info-item">
                                            <Users className="info-icon" />
                                            <div>
                                                <label>수용 인원</label>
                                                <p>{facility.capacity}</p>
                                            </div>
                                        </div>
                                        <div className="info-item">
                                            <MapPin className="info-icon" />
                                            <div>
                                                <label>위치</label>
                                                <p>{facility.location}</p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="modal-section">
                                        <h3>시설 소개</h3>
                                        <p>{facility.description}</p>
                                    </div>

                                    <div className="modal-section">
                                        <h3>보유 장비</h3>
                                        <ul className="equipment-list">
                                            {facility.equipment.map((item, index) => (
                                                <li key={index}>
                                                    <CheckCircle size={16} color="var(--color-accent-hover)" />
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    {facility.subItems && (
                                        <div className="modal-section">
                                            <h3>상세 정보</h3>
                                            <div className="sub-items-grid">
                                                {facility.subItems.map((item) => (
                                                    <button
                                                        key={item.id}
                                                        className="sub-item-btn"
                                                        onClick={() => handleSubItemClick(item)}
                                                    >
                                                        <FileText size={20} />
                                                        <span>{item.title}</span>
                                                        <ChevronRight size={16} className="arrow" />
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}


                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="sub-detail"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                className="modal-sub-view"
                            >
                                <div className="sub-view-header">
                                    <button className="back-btn" onClick={handleBack}>
                                        <ArrowLeft size={20} />
                                        뒤로가기
                                    </button>
                                    <h2>{selectedSubItem.title}</h2>
                                </div>
                                <div className="sub-view-content">
                                    {selectedSubItem.type === 'rich-content' ? (
                                        <div className="rich-content-grid">
                                            {selectedSubItem.sections.map((section, index) => (
                                                <motion.div
                                                    key={index}
                                                    className="spec-card"
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={{ delay: index * 0.1 }}
                                                    style={{
                                                        borderLeftColor: section.color,
                                                        '--section-color': section.color
                                                    }}
                                                >
                                                    <h3 style={{ color: section.color }}>
                                                        {section.title}
                                                        {section.subTitle && <span className="spec-subtitle">{section.subTitle}</span>}
                                                    </h3>
                                                    <ul>
                                                        {section.items.map((item, i) => (
                                                            <li key={i}>{item}</li>
                                                        ))}
                                                    </ul>
                                                </motion.div>
                                            ))}
                                        </div>
                                    ) : selectedSubItem.type === 'image-gallery' ? (
                                        <div className="gallery-container">
                                            <p className="gallery-description">{selectedSubItem.description}</p>
                                            <div className="gallery-grid">
                                                {selectedSubItem.images.map((img, index) => (
                                                    <motion.div
                                                        key={index}
                                                        className="gallery-item"
                                                        initial={{ opacity: 0, scale: 0.9 }}
                                                        animate={{ opacity: 1, scale: 1 }}
                                                        transition={{ delay: index * 0.1 }}
                                                        whileHover={{ scale: 1.02 }}
                                                    >
                                                        <img src={img.url} alt={img.caption} />
                                                        <div className="gallery-caption">{img.caption}</div>
                                                    </motion.div>
                                                ))}
                                            </div>
                                        </div>
                                    ) : selectedSubItem.type === 'file-download' ? (
                                        <div className="download-container">
                                            <div className="download-guide">
                                                <h3><FileText size={20} /> 제작 가이드</h3>
                                                <p className="guide-intro">{selectedSubItem.description}</p>
                                                <ul className="guide-list">
                                                    {selectedSubItem.guideLines.map((line, index) => (
                                                        <li key={index}>{line}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                            <div className="download-items">
                                                <h3><Download size={20} /> 샘플 파일 다운로드</h3>
                                                <div className="download-grid">
                                                    {selectedSubItem.downloads.map((file, index) => (
                                                        <motion.div
                                                            key={index}
                                                            className="download-card"
                                                            whileHover={{ y: -5 }}
                                                        >
                                                            <div className="file-preview">
                                                                <img src={file.previewUrl} alt={file.name} />
                                                            </div>
                                                            <div className="file-info">
                                                                <h4>{file.name}</h4>
                                                                <span className="file-size">{file.size}</span>
                                                                <a href={file.fileUrl} download className="btn-download">
                                                                    <Download size={16} /> 다운로드
                                                                </a>
                                                            </div>
                                                        </motion.div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="content-placeholder">
                                            <FileText size={48} color="var(--color-primary)" />
                                            <p>{selectedSubItem.content}</p>
                                            <button className="btn-secondary">
                                                파일 다운로드 / 자세히 보기
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </motion.div>


            {/* Zoomed Image Modal */}
            <AnimatePresence>
                {isZoomed && (
                    <motion.div
                        className="image-zoom-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsZoomed(false)}
                    >
                        <motion.div
                            className="image-zoom-content"
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.8, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button className="zoom-close-btn" onClick={() => setIsZoomed(false)}>
                                <X size={32} />
                            </button>
                            <img
                                src={facility.images ? facility.images[currentImageIndex] : facility.image}
                                alt="Zoomed View"
                            />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </AnimatePresence >
    );
};

export default FacilityModal;
