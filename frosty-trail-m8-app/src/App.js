import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/pages/Home';
import About from './components/pages/About';
import Footer from './components/Footer';

import './App.css';
import './components/CCStyles/Navbar.css';
import './components/CCStyles/Footer.css';

function App() {
  return (
    <>
      <Router>
      <Navbar />
        <Routes>
          <Route exact path='/' element={<Home />} />
          <Route path='/About' element={<About />} />
        </Routes>
        <Footer />
      </Router>
    </>
  );
}

export default App;