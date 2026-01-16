import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { facilities, buildings } from '../data/facilities';
import FacilityCard from '../components/facilities/FacilityCard';
import FacilityModal from '../components/facilities/FacilityModal';
import PageTransition from '../components/layout/PageTransition';
import { Search } from 'lucide-react';
import './Facilities.css';

const Facilities = () => {
    const [activeBuilding, setActiveBuilding] = useState('main');
    const [selectedFacility, setSelectedFacility] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const location = useLocation();
    const navigate = useNavigate();

    // Sync modal with URL ?facility=...
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const facilityId = params.get('facility') || params.get('type'); // Support 'type' for legacy or 'facility'

        if (facilityId) {
            const facility = facilities.find(f => f.id === facilityId);
            if (facility) {
                setActiveBuilding(facility.building);
                setSelectedFacility(facility);
                return;
            }
        }

        setSelectedFacility(null);
    }, [location.search]);

    const handleSelectFacility = (facility) => {
        // Update URL to open modal
        navigate(`?facility=${facility.id}`);
    };

    const handleCloseModal = () => {
        // Clear URL param to close modal
        navigate('/facilities');
    };

    const filteredFacilities = facilities.filter(f => {
        const matchesBuilding = f.building === activeBuilding;
        const matchesSearch = f.name.includes(searchTerm) ||
            f.description.includes(searchTerm) ||
            f.equipment.some(e => e.includes(searchTerm));
        return matchesBuilding && matchesSearch;
    });

    return (
        <PageTransition>
            <div className="facilities-page container">
                <div className="page-header">
                    <motion.h1 className="kinetic-title">
                        {"시설 안내".split("").map((char, index) => (
                            <motion.span
                                key={index}
                                initial={{ opacity: 0, scale: 0.5 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{
                                    delay: 0.1 + index * 0.08,
                                    duration: 0.4,
                                    ease: "easeOut"
                                }}
                            >
                                {char === " " ? "\u00A0" : char}
                            </motion.span>
                        ))}
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8, duration: 0.5 }}
                    >
                        NH 방송운영단의 시설을 본관과 신관으로 나누어 소개합니다.
                    </motion.p>
                </div>

                <div className="facilities-controls">
                    <div className="building-tabs">
                        {buildings.map(b => (
                            <button
                                key={b.id}
                                className={`building-tab ${activeBuilding === b.id ? 'active' : ''}`}
                                onClick={() => setActiveBuilding(b.id)}
                            >
                                {b.name}
                                {activeBuilding === b.id && (
                                    <motion.div
                                        className="active-tab-indicator"
                                        layoutId="activeBuildingTab"
                                    />
                                )}
                            </button>
                        ))}
                    </div>

                    <div className="search-wrapper">
                        <Search size={20} className="search-icon" />
                        <input
                            type="text"
                            placeholder="장소 검색.."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                </div>

                <motion.div
                    className="facilities-grid"
                    layout
                >
                    <AnimatePresence mode="popLayout">
                        {filteredFacilities.map((facility, index) => (
                            <FacilityCard
                                key={facility.id}
                                facility={facility}
                                index={index}
                                onClick={handleSelectFacility}
                            />
                        ))}
                    </AnimatePresence>
                </motion.div>

                {filteredFacilities.length === 0 && (
                    <div className="no-results">
                        <p>검색 결과가 없습니다.</p>
                    </div>
                )}

                {selectedFacility && (
                    <FacilityModal
                        facility={selectedFacility}
                        onClose={handleCloseModal}
                    />
                )}
            </div>
        </PageTransition>
    );
};

export default Facilities;
