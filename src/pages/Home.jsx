import React from 'react';
import HeroSection from '../components/home/HeroSection';
import QuickAccess from '../components/home/QuickAccess';
import PageTransition from '../components/layout/PageTransition';

const Home = () => {
    return (
        <PageTransition>
            <HeroSection />
            <QuickAccess />
        </PageTransition>
    );
};

export default Home;
