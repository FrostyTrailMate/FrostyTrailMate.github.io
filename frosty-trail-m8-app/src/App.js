import React from 'react';
import './App.css';
import Navbar from './components/Navbar';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Home from './components/pages/Home';
import About from './components/pages/About';
import Footer from './components/Footer';

function App() {
  return (
    <>
      <Router>
      <Navbar/>
        <Routes>
          <Route exact path='/' element={<Home />} />
          <Route path='/About' element={<About />} />
        </Routes>
        <Footer/>
      </Router>
    </>
  );
}

export default App;

