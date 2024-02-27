import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Results from './components/pages/Results';
import Create from './components/pages/Create';
import About from './components/pages/About';
import Footer from './components/Footer';

import './App.css';
import './components/CSStyles/Navbar.css';
import './components/CSStyles/Footer.css';

function App() {
  return (
    <>
      <Router>
      <Navbar />
        <Routes>
          <Route path='/' element={<Create />} />
          <Route exact path='/Results' element={<Results />} />
          <Route path='/About' element={<About />} />
        </Routes>
        <Footer />
      </Router>
    </>
  );
}

export default App;