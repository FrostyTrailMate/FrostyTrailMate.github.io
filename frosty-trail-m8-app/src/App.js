import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/pages/Home';
import About from './components/pages/About';
import Footer from './components/Footer';
import Create from './components/pages/Create';

import './App.css';
import './components/CCStyles/Navbar.css';
import './components/CCStyles/Footer.css';

function App() {
  return (
    <>
      <Router>
      <Navbar />
        <Routes>
          <Route exact path='/Home' element={<Home />} />
          <Route path='/About' element={<About />} />
          <Route path='/Create' element={<Create />} />
        </Routes>
        <Footer />
      </Router>
    </>
  );
}

export default App;