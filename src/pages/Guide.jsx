import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, FileText, Info, MapPin, Clock, AlertCircle } from 'lucide-react';
import PageTransition from '../components/layout/PageTransition';
import './Guide.css';

// Animation Variants
const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.2,
            delayChildren: 0.1
        }
    }
};

const itemFadeUp = {
    hidden: { y: 20, opacity: 0 },
    visible: {
        y: 0,
        opacity: 1,
        transition: { type: "spring", stiffness: 100 }
    }
};

const processCardHover = {
    scale: 1.05,
    y: -5,
    boxShadow: "0px 10px 20px rgba(0,0,0,0.2)",
    transition: { duration: 0.3 }
};

const Guide = () => {
    const [activeTab, setActiveTab] = useState('usage');

    const tabs = [
        { id: 'usage', label: '이용 안내', icon: <Info size={20} /> },
        { id: 'meeting', label: '회의/행사 문의', icon: <Phone size={20} /> },
        { id: 'facility', label: '부대시설 문의', icon: <MapPin size={20} /> },
    ];

    return (
        <PageTransition>
            <motion.div
                className="guide-page container"
                initial="hidden"
                animate="visible"
                variants={containerVariants}
            >
                <div className="page-header">
                    <motion.h1 className="kinetic-title">
                        {"이용 안내".split("").map((char, index) => (
                            <motion.span
                                key={index}
                                initial={{ opacity: 0, y: 50, rotateX: -90 }}
                                animate={{ opacity: 1, y: 0, rotateX: 0 }}
                                transition={{
                                    delay: 0.2 + index * 0.08,
                                    type: "spring",
                                    stiffness: 120,
                                    damping: 10
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
                        방송운영단 시설 이용 및 문의처를 안내해 드립니다.
                    </motion.p>
                </div>

                <div className="tabs-container">
                    <motion.div className="tabs-header" variants={itemFadeUp}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                {tab.icon}
                                <span>{tab.label}</span>
                                {activeTab === tab.id && (
                                    <motion.div
                                        className="active-indicator"
                                        layoutId="activeTab"
                                    />
                                )}
                            </button>
                        ))}
                    </motion.div>

                    <motion.div className="tab-content" variants={itemFadeUp}>
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeTab}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                            >
                                {activeTab === 'usage' && <UsageGuide />}
                                {activeTab === 'meeting' && <MeetingContact />}
                                {activeTab === 'facility' && <FacilityContact />}
                            </motion.div>
                        </AnimatePresence>
                    </motion.div>
                </div>
            </motion.div>
        </PageTransition>
    );
};

const alertBoxVariant = {
    hidden: { y: 20, opacity: 0 },
    visible: {
        y: 0,
        opacity: 1,
        transition: {
            delay: 1.2,
            type: "spring",
            stiffness: 100
        }
    }
};

const UsageGuide = () => (
    <motion.div
        className="guide-content"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
    >
        <section className="guide-section">
            <motion.h2 variants={itemFadeUp}><FileText className="section-icon" /> 회의장 이용 절차</motion.h2>
            <motion.div
                className="process-steps"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, amount: 0.3 }}
                variants={{
                    hidden: { opacity: 0 },
                    visible: {
                        opacity: 1,
                        transition: { staggerChildren: 0.15 }
                    }
                }}
            >
                <motion.div
                    className="step"
                    variants={{
                        hidden: { opacity: 0, y: 40, scale: 0.95 },
                        visible: { opacity: 1, y: 0, scale: 1 }
                    }}
                    whileHover={processCardHover}
                >
                    <span className="step-num">01</span>
                    <h3>예약 작성</h3>
                    <p>아리오피스 &gt; 회의실 관리 &gt; 회의장 예약 작성</p>
                </motion.div>
                <motion.div
                    className="step-arrow"
                    variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}
                >→</motion.div>
                <motion.div
                    className="step"
                    variants={{
                        hidden: { opacity: 0, y: 40, scale: 0.95 },
                        visible: { opacity: 1, y: 0, scale: 1 }
                    }}
                    whileHover={processCardHover}
                >
                    <span className="step-num">02</span>
                    <h3>신청서 송부</h3>
                    <p>방송사용 신청서 작성 후 담당자에게 송부</p>
                    <div className="contact-box">
                        <p><strong>본관 총무팀:</strong> 정욱종 과장(6011), 최여진 주임(6007)</p>
                        <p><strong>신관 총무팀:</strong> 배소영 과장보(4373)</p>
                    </div>
                </motion.div>
                <motion.div
                    className="step-arrow"
                    variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}
                >→</motion.div>
                <motion.div
                    className="step"
                    variants={{
                        hidden: { opacity: 0, y: 40, scale: 0.95 },
                        visible: { opacity: 1, y: 0, scale: 1 }
                    }}
                    whileHover={processCardHover}
                >
                    <span className="step-num">03</span>
                    <h3>사전 협의</h3>
                    <p>대강당 대형행사 시 사전협의 필수</p>
                </motion.div>
            </motion.div>
            <motion.div
                className="alert-box"
                variants={alertBoxVariant}
                whileHover={{ scale: 1.02 }}
            >
                <AlertCircle size={20} />
                <p>신청 후 승인된 회의/행사에 한해서만 지원 가능하며, 구두 예약은 방송 지원이 불가합니다.</p>
            </motion.div>
        </section>

        <section className="guide-section">
            <motion.div variants={itemFadeUp}>
                <h2><Clock className="section-icon" /> 방송실 지원 시간</h2>
                <ul className="time-list">
                    <li>
                        <strong>평일:</strong> 09:00 ~ 12:00 / 13:00 ~ 18:00
                    </li>
                    <li>
                        <strong>휴일:</strong> 부득이한 경우 별도 협의 필요
                    </li>
                    <li>
                        <strong>기타:</strong> 회의 시작 1시간 전 직원 대기, 30분 전 경음악 송출 (점심시간 제외)
                    </li>
                </ul>
            </motion.div>
        </section>

        <section className="guide-section">
            <motion.div variants={itemFadeUp}>
                <h2><Info className="section-icon" /> 기타 안내</h2>
                <ul className="info-list">
                    <li>각 회의장별 지원 내용은 "방송장비 이용 가능 현황"을 참고해 주시기 바랍니다.</li>
                    <li>신 화상회의 시스템은 사용자 측에서 직접 운영합니다.</li>
                    <li>문의사항: <strong>방송운영단 2080-5994</strong></li>
                </ul>
            </motion.div>
        </section>
    </motion.div>
);

const MeetingContact = () => (
    <div className="guide-content">
        <div className="contact-grid">
            <ContactCard index={0} title="방송기술 지원" phone="5994" sub="(신관 7112,3)" dept="방송운영단" />
            <ContactCard index={1} title="중요행사 협의" phone="5993" dept="방송운영단" />
            <ContactCard index={2} title="좌석 배치" phone="5979" sub="(신관 4397)" dept="용원실" />
            <ContactCard index={3} title="이동식 칸막이" phone="5981" dept="건축실" />
            <ContactCard index={4} title="DID식순, 화상회의" phone="6011" dept="총무팀" />
        </div>
    </div>
);

const FacilityContact = () => (
    <div className="guide-content">
        <div className="contact-grid">
            <ContactCard index={0} title="인터넷 설치" phone="6998" sub="(외부망)" dept="헬프데스크" />
            <ContactCard index={1} title="인터넷 설치" phone="5995" sub="(내부망)" dept="통신운영실" />
            <ContactCard index={2} title="차량출입, 주차안내" phone="5802" sub="(신관 7132)" dept="보안실" />
            <ContactCard index={3} title="냉난방 공조" phone="5119" sub="(신관 7119)" dept="중앙관제실" />
            <ContactCard index={4} title="안내방송, 유튜브중계" phone="5733~4" sub="로비대형스크린" dept="농협방송국" />
            <ContactCard index={5} title="꽃, 화분" phone="5982" dept="조경실" />
            <ContactCard index={6} title="화장실 / 음식물 처리" phone="4156" dept="관리실" />
        </div>
    </div>
);

const ContactCard = ({ index = 0, title, phone, sub, dept }) => {
    const [rotateX, setRotateX] = React.useState(0);
    const [rotateY, setRotateY] = React.useState(0);
    const [isHovered, setIsHovered] = React.useState(false);

    const handleMouseMove = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = (e.clientY - rect.top - rect.height / 2) / 12;
        const y = -(e.clientX - rect.left - rect.width / 2) / 12;
        setRotateX(x);
        setRotateY(y);
    };

    const handleMouseLeave = () => {
        setRotateX(0);
        setRotateY(0);
        setIsHovered(false);
    };

    return (
        <motion.div
            className="contact-card-wrapper"
            style={{ perspective: 1000 }}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={handleMouseLeave}
        >
            <motion.div
                className={`contact-card ${isHovered ? 'card-glow' : ''}`}
                initial={{ opacity: 0, y: 40, scale: 0.9, rotateX: 15 }}
                animate={{
                    opacity: 1,
                    y: 0,
                    scale: 1,
                    rotateX: isHovered ? rotateX : 0,
                    rotateY: isHovered ? rotateY : 0
                }}
                transition={{
                    opacity: { duration: 0.4, delay: index * 0.08 },
                    y: { duration: 0.4, delay: index * 0.08, type: "spring", stiffness: 100 },
                    scale: { duration: 0.4, delay: index * 0.08 },
                    rotateX: { type: "spring", stiffness: 400, damping: 25 },
                    rotateY: { type: "spring", stiffness: 400, damping: 25 }
                }}
                whileHover={{
                    scale: 1.05,
                    y: -8,
                    boxShadow: "0px 20px 40px rgba(0,53,148,0.25)"
                }}
            >
                <div className="card-shimmer" />
                <h3>{title}</h3>
                <div className="contact-info">
                    <span className="phone">{phone}</span>
                    <span className="sub">{sub || "\u00A0"}</span>
                </div>
                <span className="dept">{dept}</span>
            </motion.div>
        </motion.div>
    );
};

export default Guide;
