import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, addDays, isSameMonth, isSameDay, isToday, parseISO, isValid } from 'date-fns';
import { ko } from 'date-fns/locale';
import './Schedule.css';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, MapPin, Clock, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchEvents } from '../services/googleCalendar';

const Schedule = () => {
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [events, setEvents] = useState([]);
    const [holidays, setHolidays] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const location = useLocation();
    const navigate = useNavigate();

    // Sync modal with URL ?date=YYYY-MM-DD
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const dateStr = params.get('date');

        if (dateStr) {
            const parsedDate = parseISO(dateStr);
            if (isValid(parsedDate)) {
                setSelectedDate(parsedDate);
                setIsModalOpen(true);
                return;
            }
        }

        setIsModalOpen(false);
    }, [location.search]);

    // Korean Public Holidays (Fixed dates for demo)
    const getHolidays = (year) => {
        return {
            [`${year}-01-01`]: '신정',
            [`${year}-03-01`]: '삼일절',
            [`${year}-05-05`]: '어린이날',
            [`${year}-06-06`]: '현충일',
            [`${year}-08-15`]: '광복절',
            [`${year}-10-03`]: '개천절',
            [`${year}-10-09`]: '한글날',
            [`${year}-12-25`]: '크리스마스',
        };
    };

    useEffect(() => {
        const year = currentMonth.getFullYear();
        setHolidays(getHolidays(year));
        loadEvents();
    }, [currentMonth]);

    const loadEvents = async () => {
        setLoading(true);
        setError(null);
        try {
            const start = startOfWeek(startOfMonth(currentMonth));
            const end = endOfWeek(endOfMonth(currentMonth));
            const fetchedEvents = await fetchEvents(start, end);
            setEvents(fetchedEvents);
        } catch (error) {
            console.error("Failed to load events", error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const nextMonth = () => {
        setCurrentMonth(addDays(endOfMonth(currentMonth), 1));
    };

    const prevMonth = () => {
        setCurrentMonth(addDays(startOfMonth(currentMonth), -1));
    };

    const onDateClick = (day) => {
        // Update URL to open modal
        navigate(`?date=${format(day, 'yyyy-MM-dd')}`);
    };

    const closeModal = () => {
        // Clear URL param to close modal
        navigate('/schedule');
    };

    const renderHeader = () => {
        const dateFormat = "yyyy년 M월";

        return (
            <div className="calendar-header">
                <div className="header-left">
                    <h2>{format(currentMonth, dateFormat, { locale: ko })}</h2>
                </div>
                <div className="header-nav">
                    <button className="nav-btn" onClick={prevMonth}>
                        <ChevronLeft size={24} />
                    </button>
                    <button className="today-btn" onClick={() => setCurrentMonth(new Date())}>
                        오늘
                    </button>
                    <button className="nav-btn" onClick={nextMonth}>
                        <ChevronRight size={24} />
                    </button>
                </div>
            </div>
        );
    };

    const renderDays = () => {
        const days = ["일", "월", "화", "수", "목", "금", "토"];
        return (
            <div className="days-row">
                {days.map((day, i) => (
                    <div className={`day-name ${i === 0 ? 'sunday' : i === 6 ? 'saturday' : ''}`} key={i}>
                        {day}
                    </div>
                ))}
            </div>
        );
    };

    const renderCells = () => {
        const monthStart = startOfMonth(currentMonth);
        const monthEnd = endOfMonth(monthStart);
        const startDate = startOfWeek(monthStart);
        const endDate = endOfWeek(monthEnd);

        const dateFormat = "d";
        const rows = [];
        let days = [];
        let day = startDate;
        let formattedDate = "";

        while (day <= endDate) {
            for (let i = 0; i < 7; i++) {
                formattedDate = format(day, dateFormat);
                const cloneDay = day;

                const isHoliday = holidays[format(day, 'yyyy-MM-dd')];
                const dayEvents = events.filter(e => isSameDay(e.start, day));

                days.push(
                    <div
                        className={`cell ${!isSameMonth(day, monthStart)
                            ? "disabled"
                            : isSameDay(day, selectedDate) ? "selected" : ""
                            }`}
                        key={day}
                        onClick={() => onDateClick(cloneDay)}
                    >
                        <div className="cell-header">
                            <span className={`number ${i === 0 ? 'sunday' : i === 6 ? 'saturday-text' : ''} ${isHoliday ? 'holiday-text' : ''}`}>
                                {formattedDate}
                            </span>
                            {isHoliday && <span className="holiday-name">{isHoliday}</span>}
                        </div>
                        <div className="events-container">
                            {dayEvents.map((event, idx) => (
                                <div key={idx} className="event-pill" style={{ backgroundColor: event.color || '#37bc9b' }}>
                                    {!event.allDay && <span className="event-time-badge">{format(event.start, 'HH:mm')}</span>}
                                    <span className="event-title-text">{event.title}</span>
                                    {event.location && <span className="event-location-text">{event.location}</span>}
                                </div>
                            ))}
                        </div>
                    </div>
                );
                day = addDays(day, 1);
            }
            rows.push(
                <div className="row" key={day}>
                    {days}
                </div>
            );
            days = [];
        }
        return <div className="calendar-body">{rows}</div>;
    };

    const renderModal = () => {
        if (!isModalOpen) return null;

        const selectedDayEvents = events.filter(e => isSameDay(e.start, selectedDate));
        const holidayName = holidays[format(selectedDate, 'yyyy-MM-dd')];

        return (
            <AnimatePresence>
                {isModalOpen && (
                    <>
                        <motion.div
                            className="modal-backdrop"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={closeModal}
                        />
                        <div className="modal-wrapper">
                            <motion.div
                                className="day-schedule-modal"
                                initial={{ opacity: 0, y: 50, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 20, scale: 0.95 }}
                                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                            >
                                <button className="modal-close-btn" onClick={closeModal}>
                                    <X size={24} />
                                </button>

                                <div className="modal-header">
                                    <div className="date-display">
                                        <span className="date-day">{format(selectedDate, 'd')}</span>
                                        <div className="date-meta">
                                            <span className="date-month">{format(selectedDate, 'M월')}</span>
                                            <span className="date-weekday">{format(selectedDate, 'EEEE', { locale: ko })}</span>
                                        </div>
                                    </div>
                                    {holidayName && <div className="modal-holiday-badge">{holidayName}</div>}
                                </div>

                                <div className="modal-body">
                                    <h3>일정 목록</h3>
                                    <div className="event-list">
                                        {selectedDayEvents.length > 0 ? (
                                            selectedDayEvents.map((event, idx) => (
                                                <div key={idx} className="event-item">
                                                    <div className="event-time">
                                                        <Clock size={14} />
                                                        {event.allDay ? (
                                                            '종일'
                                                        ) : (
                                                            <>
                                                                {format(event.start, 'HH:mm')}
                                                                <span className="time-separator"> ~ </span>
                                                                {format(event.end, 'HH:mm')}
                                                            </>
                                                        )}
                                                    </div>
                                                    <div className="event-title">{event.title}</div>
                                                    {event.description && (
                                                        <div className="event-description">
                                                            {event.description}
                                                        </div>
                                                    )}
                                                    {event.location && (
                                                        <div className="event-location">
                                                            <MapPin size={14} />
                                                            {event.location}
                                                        </div>
                                                    )}
                                                </div>
                                            ))
                                        ) : (
                                            <div className="no-events">
                                                등록된 일정이 없습니다.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    </>
                )}
            </AnimatePresence>
        );
    };

    return (
        <div className="schedule-page">
            <div className="calendar-container">
                {renderHeader()}
                {renderDays()}
                {error && (
                    <div className="error-message" style={{ color: '#ff6b6b', textAlign: 'center', padding: '1rem', background: 'rgba(255, 107, 107, 0.1)', borderRadius: '8px', marginBottom: '1rem' }}>
                        ⚠️ 일정 불러오기 실패: {error}
                        <br />
                        <small>구글 캘린더가 '공개' 상태인지 확인해주세요.</small>
                    </div>
                )}
                {loading ? (
                    <div className="loading-state">
                        <div className="spin"><CalendarIcon size={40} /></div>
                    </div>
                ) : (
                    renderCells()
                )}
            </div>
            {renderModal()}
        </div>
    );
};

export default Schedule;
