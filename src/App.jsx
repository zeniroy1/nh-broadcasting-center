import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import About from './pages/About';
import Facilities from './pages/Facilities';
import Schedule from './pages/Schedule';
import StatusBoard from './pages/StatusBoard';
import Guide from './pages/Guide';

const AnimatedRoutes = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/guide" element={<Guide />} />
        <Route path="/facilities" element={<Facilities />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/status" element={<StatusBoard />} />
      </Routes>
    </AnimatePresence>
  );
};

function App() {
  return (
    <Router>
      <Layout>
        <AnimatedRoutes />
      </Layout>
    </Router>
  );
}

export default App;
